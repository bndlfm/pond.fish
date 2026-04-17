# -*- coding: utf-8 -*-

import json
import sys
import argparse
import os
import re
import subprocess
import shlex

def get_config_setting(name):
    try:
        from fish_ai.config import get_config
        return get_config(name)
    except:
        return None

DEBUG_ENABLED = get_config_setting('debug') == 'True'

def debug_log(msg):
    if DEBUG_ENABLED:
        sys.stderr.write(f"DEBUG: {msg}\n")
        sys.stderr.flush()

def get_skills_dir():
    from fish_ai.engine import get_install_dir
    path = os.path.join(os.path.dirname(get_install_dir()), 'fish-ai', 'skills')
    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)
        except:
            pass
    return path

class SkillManager:
    def __init__(self):
        self.skills_dir = get_skills_dir()
        self.catalog = {} # name -> description
        self.tools = []   # list of OpenAI-style tool definitions
        self.discover_skills()

    def discover_skills(self):
        if not os.path.exists(self.skills_dir):
            return
        
        for item in os.listdir(self.skills_dir):
            skill_path = os.path.join(self.skills_dir, item)
            if not os.path.isdir(skill_path):
                continue
            
            # 1. Parse metadata
            skill_md_path = os.path.join(skill_path, 'SKILL.md')
            skill_name = item # Default to folder name
            if os.path.exists(skill_md_path):
                try:
                    with open(skill_md_path, 'r') as f:
                        content = f.read()
                        m = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                        if m:
                            frontmatter = m.group(1)
                            for line in frontmatter.splitlines():
                                if line.startswith('name:'):
                                    skill_name = line.split(':', 1)[1].strip()
                                if line.startswith('description:'):
                                    self.catalog[skill_name] = line.split(':', 1)[1].strip()
                except Exception as e:
                    debug_log(f"Error parsing SKILL.md in {item}: {e}")

            # 2. Discover scripts
            scripts_dir = os.path.join(skill_path, 'scripts')
            if os.path.exists(scripts_dir):
                for script in os.listdir(scripts_dir):
                    script_path = os.path.join(scripts_dir, script)
                    if os.access(script_path, os.X_OK):
                        try:
                            # Run with --info to get tool schema
                            result = subprocess.run([script_path, '--info'], capture_output=True, text=True)
                            if result.returncode == 0:
                                schema = json.loads(result.stdout)
                                # Prepend skill name to tool name to prevent collisions
                                tool_name = f"skill__{skill_name}__{schema['name']}"
                                schema['name'] = tool_name
                                self.tools.append({"type": "function", "function": schema})
                                debug_log(f"Registered tool: {tool_name}")
                        except Exception as e:
                            debug_log(f"Error registering tool from {script}: {e}")

    def get_catalog_prompt(self):
        if not self.catalog:
            return ""
        prompt = "\nAVAILABLE SKILLS:\n"
        for name, desc in self.catalog.items():
            prompt += f"- {name}: {desc}\n"
        prompt += "\nTo see full instructions for a skill, call 'activate_skill(name)'.\n"
        return prompt

    def get_skill_body(self, name):
        # Look for SKILL.md by name in subdirectories
        for item in os.listdir(self.skills_dir):
            skill_md_path = os.path.join(self.skills_dir, item, 'SKILL.md')
            if os.path.exists(skill_md_path):
                with open(skill_md_path, 'r') as f:
                    if f'name: {name}' in f.read(512):
                        f.seek(0)
                        content = f.read()
                        return re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL).strip()
        return None

    def execute_skill_tool(self, tool_name, arguments):
        # Format: skill__skillname__scriptname
        parts = tool_name.split('__', 2)
        if len(parts) < 3: return f"Error: Invalid tool name format {tool_name}"
        skill_name, script_name = parts[1], parts[2]
        
        # Locate script
        for item in os.listdir(self.skills_dir):
            script_path = os.path.join(self.skills_dir, item, 'scripts', script_name)
            if os.path.exists(script_path):
                try:
                    # Pass arguments as environment variables
                    env = os.environ.copy()
                    for k, v in arguments.items():
                        env[str(k)] = str(v)
                    
                    result = subprocess.run([script_path], capture_output=True, text=True, env=env)
                    return result.stdout if result.returncode == 0 else f"Error ({result.returncode}): {result.stderr}"
                except Exception as e:
                    return f"Execution error: {str(e)}"
        return f"Error: Could not find script for {tool_name}"

def read_path(path):
    try:
        if os.path.isdir(path):
            items = os.listdir(path)
            return f"Directory listing for {path}:\n" + "\n".join(items)
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return str(e)

def web_search(query):
    api_key = get_config_setting('brave_search_api_key')
    if not api_key:
        return "Error: Brave Search API key not configured."
    try:
        import httpx
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
        params = {"q": query, "count": 5}
        response = httpx.get(url, headers=headers, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        results = []
        for result in data.get('web', {}).get('results', []):
            snippet = result.get('description', 'No description.')
            snippet_lines = snippet.splitlines()
            if len(snippet_lines) > 2: snippet = "\n".join(snippet_lines[:2]) + "..."
            results.append(f"Title: {result.get('title')}\nURL: {result.get('url')}\nSnippet: {snippet}\n")
        return "\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search error: {str(e)}"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "shell_execute",
            "description": "Execute a command in the fish shell.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "The shell command to execute."}},
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_path",
            "description": "Read the content of a file or list the contents of a directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "The path to the file or directory."}},
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web using Brave Search for documentation or troubleshooting help.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "The search query."}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "activate_skill",
            "description": "Load the detailed instructions for a specific skill from the catalog.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "The name of the skill to activate."}},
                "required": ["name"]
            }
        }
    }
]

SYSTEM_PROMPT = """
You are an expert coding assistant working inside a fish shell.
Your goal is to achieve the user's request by using the provided tools.

MANDATORY AUDIT RULES:
1. ALWAYS provide a concise 'Thought' explaining YOUR CURRENT PLAN before calling any tool.
2. Use `shell_execute` for all shell commands. They will run in the user's ACTIVE session.
3. Use `read_path` for direct file system access.
4. Use `web_search` for any information you don't have locally.
5. Work through your plan turn-by-turn. Provide a final summary of your findings or actions when complete.
"""

def main():
    try:
        from fish_ai.engine import get_chat_response, get_os, get_logger
        parser = argparse.ArgumentParser()
        parser.add_argument('--state', required=True)
        parser.add_argument('--action-file', required=True)
        parser.add_argument('--goal')
        parser.add_argument('--external-history')
        parser.add_argument('--cwd')
        parser.add_argument('--last-output')
        parser.add_argument('--last-status', type=int)
        parser.add_argument('--rejected', action='store_true')
        parser.add_argument('--compress', action='store_true')
        parser.add_argument('--json', action='store_true')

        args = parser.parse_args()
        
        skill_manager = SkillManager()
        
        messages = []
        if os.path.exists(args.state) and os.path.getsize(args.state) > 0:
            with open(args.state, 'r') as f:
                try: messages = json.load(f)
                except: messages = []
        
        if not messages:
            full_prompt = SYSTEM_PROMPT + skill_manager.get_catalog_prompt() + "\nOperating System: {os}\n".format(os=get_os())
            messages = [{'role': 'system', 'content': full_prompt}]
            context_msg = "Context:\n"
            if args.cwd: context_msg += f"- Current directory: {args.cwd}\n"
            if args.external_history: context_msg += f"- Recent shell history:\n{args.external_history}\n"
            if args.cwd or args.external_history:
                messages.append({'role': 'user', 'content': context_msg})
                messages.append({'role': 'assistant', 'content': "Understood."})
        
        if args.goal:
            messages.append({'role': 'user', 'content': args.goal})
        elif not messages or len(messages) <= 1:
            messages.append({'role': 'user', 'content': 'Ready.'})

        if args.rejected:
            messages.append({'role': 'user', 'content': 'I rejected that command.'})
        elif args.last_output is not None:
            content = args.last_output
            if args.last_status is not None: content = f"Exit status: {args.last_status}\n\nOutput:\n{content}"
            last_id = next((m['tool_calls'][0]['id'] for m in reversed(messages) if m.get('role') == 'assistant' and m.get('tool_calls')), None)
            if last_id: messages.append({'role': 'tool', 'tool_call_id': last_id, 'content': content})
            else: messages.append({'role': 'user', 'content': content})

        # Combine native tools with skill-provided tools
        combined_tools = TOOLS + skill_manager.tools

        response = get_chat_response(messages, tools=combined_tools)
        if not response: raise Exception("AI returned empty response.")

        if args.json:
            print(json.dumps(response, indent=2))
            sys.exit(0)

        messages.append(response)
        with open(args.state, 'w') as f: json.dump(messages, f)

        full_content = response.get('content', '')
        remaining_content = full_content
        thought = ""
        
        if '<think>' in full_content:
            m = re.search(r'<think>(.*?)</think>(.*)', full_content, re.DOTALL)
            if m:
                thought = m.group(1).strip()
                remaining_content = m.group(2).strip()
        elif response.get('tool_calls'):
            thought = full_content.strip()
            remaining_content = ""

        if thought: sys.stdout.write(f"THOUGHT\n{thought}\nEND_THOUGHT\n")

        if response.get('tool_calls'):
            tool_call = response['tool_calls'][0]
            func_name = tool_call['function']['name'].split(':')[-1]
            func_args = json.loads(tool_call['function']['arguments'])

            if func_name == 'shell_execute':
                with open(args.action_file, 'w') as f: f.write(func_args['command'])
                sys.stdout.write("EXECUTE\n")
            else:
                result = ""
                if func_name == 'read_path':
                    sys.stdout.write(f"TOOL_CALL: read_path({func_args.get('path')})\n")
                    result = read_path(func_args['path'])
                elif func_name == 'web_search':
                    sys.stdout.write(f"TOOL_CALL: web_search({func_args.get('query')})\n")
                    result = web_search(func_args['query'])
                elif func_name == 'activate_skill':
                    skill_name = func_args.get('name')
                    sys.stdout.write(f"TOOL_CALL: activate_skill({skill_name})\n")
                    body = skill_manager.get_skill_body(skill_name)
                    result = f"Skill '{skill_name}' activated:\n{body}" if body else f"Error: Skill '{skill_name}' not found."
                elif func_name.startswith('skill__'):
                    # Call scripted skill tool
                    result = skill_manager.execute_skill_tool(func_name, func_args)
                else:
                    result = f"Unknown tool: {func_name}"
                
                sys.stdout.write(f"TOOL_RESULT\n{result}\nEND_RESULT\n")
                messages.append({'role': 'tool', 'tool_call_id': tool_call['id'], 'content': result})
                with open(args.state, 'w') as f: json.dump(messages, f)
                sys.stdout.write("CONTINUE\n")
        else:
            if not remaining_content and thought: remaining_content = thought
            with open(args.action_file, 'w') as f: f.write(remaining_content)
            sys.stdout.write("CHAT\n")
        
        sys.stdout.flush()
    except KeyboardInterrupt: sys.exit(130)
    except Exception as e:
        debug_log(str(e))
        with open(args.action_file, 'w') as f: f.write(str(e))
        sys.stdout.write("ERROR\n")
        sys.stdout.flush()
        sys.exit(1)

def render_markdown():
    try:
        from rich.console import Console
        from rich.markdown import Markdown
        Console().print(Markdown(sys.stdin.read() or ""))
    except: sys.stdout.write(sys.stdin.read())

if __name__ == "__main__": main()
