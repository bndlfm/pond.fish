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
    from fish_ai.config import get_config_path
    config_dir = os.path.dirname(get_config_path())
    path = os.path.join(config_dir, 'fish-ai', 'skills')
    if not os.path.exists(path):
        try: os.makedirs(path, exist_ok=True)
        except: pass
    return path

class SkillManager:
    def __init__(self):
        self.skills_dir = get_skills_dir()
        self.catalog = {} # name -> description
        self.discover_skills()

    def discover_skills(self):
        if not os.path.exists(self.skills_dir): return
        for item in os.listdir(self.skills_dir):
            skill_path = os.path.join(self.skills_dir, item)
            if not os.path.isdir(skill_path): continue
            skill_md_path = os.path.join(skill_path, 'SKILL.md')
            if os.path.exists(skill_md_path):
                try:
                    with open(skill_md_path, 'r') as f:
                        content = f.read()
                        m = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                        if m:
                            frontmatter = m.group(1)
                            name, desc = None, None
                            for line in frontmatter.splitlines():
                                if line.startswith('name:'): name = line.split(':', 1)[1].strip()
                                if line.startswith('description:'): desc = line.split(':', 1)[1].strip()
                            if name and desc:
                                self.catalog[name] = desc
                                debug_log(f"Discovered skill: {name}")
                except Exception as e: debug_log(f"Error parsing skill {item}: {e}")

    def get_catalog_text(self):
        text = f"Searching for skills in {self.skills_dir}...\n"
        if not self.catalog:
            return text + "No skills found. To add a skill, create a folder with a SKILL.md file in that directory."
        text += "Available skills:\n"
        for name, desc in self.catalog.items():
            text += f"- {name}: {desc}\n"
        return text

    def get_catalog_prompt(self):
        if not self.catalog: return ""
        prompt = "\nAVAILABLE SKILLS:\n"
        for name, desc in self.catalog.items():
            prompt += f"- {name}: {desc}\n"
        prompt += "\nTo use a skill, you MUST call 'activate_skill(name)' to see its full instructions and tool manifest.\n"
        return prompt

    def get_skill_manifest(self, name):
        target_dir = None
        for item in os.listdir(self.skills_dir):
            skill_path = os.path.join(self.skills_dir, item)
            if not os.path.isdir(skill_path): continue
            md_path = os.path.join(skill_path, 'SKILL.md')
            if os.path.exists(md_path):
                try:
                    with open(md_path, 'r') as f:
                        content_start = f.read(512)
                        if f'name: {name}' in content_start:
                            target_dir = skill_path
                            break
                except: continue
        if not target_dir: return None

        try:
            with open(os.path.join(target_dir, 'SKILL.md'), 'r') as f:
                content = f.read()
                body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL).strip()
            
            def list_files(subdir):
                path = os.path.join(target_dir, subdir)
                if os.path.exists(path):
                    return [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
                return []

            scripts = [s for s in list_files('scripts') if os.access(s, os.X_OK)]
            refs = list_files('references')
            assets = list_files('assets')
            
            manifest = f"Skill '{name}' activated.\n\nINSTRUCTIONS:\n{body}\n"
            if scripts:
                manifest += "\nAVAILABLE SCRIPTS (Execute via shell_execute):\n"
                for s in scripts: manifest += f"- {s}\n"
            if refs:
                manifest += "\nAVAILABLE REFERENCES (Examine via read_path):\n"
                for r in refs: manifest += f"- {r}\n"
            if assets:
                manifest += "\nAVAILABLE ASSETS:\n"
                for a in assets: manifest += f"- {a}\n"
            return manifest
        except Exception as e:
            return f"Error loading manifest for '{name}': {e}"

def read_path(path):
    try:
        if os.path.isdir(path):
            items = os.listdir(path)
            return f"Directory listing for {path}:\n" + "\n".join(items)
        with open(path, 'r') as f: return f.read()
    except Exception as e: return str(e)

def web_search(query):
    api_key = get_config_setting('brave_search_api_key')
    if not api_key: return "Error: Brave Search API key not configured."
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
    except Exception as e: return f"Search error: {str(e)}"

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
            "name": "list_skills",
            "description": "List all available specialized skills (experts) in the local skills directory.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "activate_skill",
            "description": "Activate a specific skill to load its detailed instructions and tool manifest.",
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
5. If the user asks about your abilities or expertise, USE `list_skills` to see what experts are installed.
6. To load the rules or scripts for a specific expert, USE `activate_skill(name)`.
7. Work through your plan turn-by-turn. Provide a final summary of your findings when complete.
"""

def compress_history(messages):
    from fish_ai.engine import get_chat_response
    if len(messages) <= 10: return messages
    system_msg = messages[0]
    initial_context = messages[1:3] if len(messages) > 3 else []
    recent_msgs = messages[-4:]
    to_summarize = messages[3:-4] if len(messages) > 7 else []
    if not to_summarize: return messages
    sys.stdout.write("STATUS: Compressing history...\n")
    sys.stdout.flush()
    summary_prompt = [
        {'role': 'system', 'content': 'Summarize the following shell actions and findings into a concise list of "Achievements so far".'},
        {'role': 'user', 'content': json.dumps(to_summarize)}
    ]
    try:
        response = get_chat_response(summary_prompt)
        summary_text = response.get('content', 'History compressed.')
        compressed_msg = {'role': 'user', 'content': f"[SYSTEM: History Compressed]\nSummary:\n{summary_text}"}
        ack_msg = {'role': 'assistant', 'content': "Understood. Resuming with previous context."}
        return [system_msg] + initial_context + [compressed_msg, ack_msg] + recent_msgs
    except: return messages

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
        if args.goal: messages.append({'role': 'user', 'content': args.goal})
        elif not messages or len(messages) <= 1: messages.append({'role': 'user', 'content': 'Hello, how can I help you today?'})
        if args.rejected: messages.append({'role': 'user', 'content': 'I rejected that command.'})
        elif args.last_output is not None:
            content = args.last_output
            if args.last_status is not None: content = f"Exit status: {args.last_status}\n\nOutput:\n{content}"
            last_id = None
            for msg in reversed(messages):
                if msg.get('role') == 'assistant' and msg.get('tool_calls'):
                    last_id = msg['tool_calls'][0]['id']
                    break
            if last_id: messages.append({'role': 'tool', 'tool_call_id': last_id, 'content': content})
            else: messages.append({'role': 'user', 'content': content})
        if args.compress or len(messages) > 20:
            messages = compress_history(messages)
            with open(args.state, 'w') as f: json.dump(messages, f)
        response = get_chat_response(messages, tools=TOOLS)
        if not response: raise Exception("AI returned empty response.")
        if args.json:
            print(json.dumps(response, indent=2))
            sys.exit(0)
        messages.append(response)
        with open(args.state, 'w') as f: json.dump(messages, f)
        full_content = response.get('content', '')
        remaining_content, thought = full_content, ""
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
            raw_func_name = tool_call['function']['name']
            func_name = raw_func_name.split(':')[-1]
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
                elif func_name == 'list_skills':
                    sys.stdout.write(f"TOOL_CALL: list_skills()\n")
                    result = skill_manager.get_catalog_text()
                elif func_name == 'activate_skill':
                    skill_name = func_args.get('name')
                    sys.stdout.write(f"SKILL_ACTIVATE: {skill_name}\n")
                    result = skill_manager.get_skill_manifest(skill_name)
                    if not result: result = f"Error: Skill '{skill_name}' not found."
                else: result = f"Unknown tool: {func_name}"
                sys.stdout.write(f"TOOL_RESULT\n{result}\nEND_RESULT\n")
                messages.append({'role': 'tool', 'tool_call_id': tool_call['id'], 'content': result})
                with open(args.state, 'w') as f: json.dump(messages, f)
                sys.stdout.write("CONTINUE\n")
        else:
            if not remaining_content and thought: remaining_content = thought
            if not remaining_content: remaining_content = "The task is complete."
            with open(args.action_file, 'w') as f: f.write(remaining_content)
            sys.stdout.write("CHAT\n")
        
        if 'usage' in response:
            u = response['usage']
            sys.stdout.write(f"USAGE: prompt={u.get('prompt_tokens', 0)} completion={u.get('completion_tokens', 0)} total={u.get('total_tokens', 0)}\n")
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
