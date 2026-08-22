#!/usr/bin/env fish
# Offline Pond 3 release smoke test. Run from an installed checkout.

set -l root (path dirname (status filename))/..
functions -e pond 2>/dev/null
source "$root/functions/pond.fish"

set -l failures 0

pond version >/dev/null
or set failures (math $failures + 1)
pond help >/dev/null
or set failures (math $failures + 1)

set -l q_output (pond -q smoke-test 2>&1)
if test $status -ne 2; or not string match -q '*pond -q was removed*' -- "$q_output"
    set failures (math $failures + 1)
end

if type -q hermes
    hermes acp --check >/dev/null 2>&1
    or set failures (math $failures + 1)
end

if test $failures -eq 0
    echo 'Pond release smoke test: PASS'
    exit 0
end

echo "Pond release smoke test: FAIL ($failures checks)" >&2
exit 1
