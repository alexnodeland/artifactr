"""Sort the imports again, under the shared ruff configuration.

With one configuration, a sibling package is first-party wherever it is imported, as the
package's own modules are, so each import that names a sibling moves into the first-party group.
The ruff the lock pins sorts them, and changes nothing else. .git-blame-ignore-revs names the
commit.
"""

from lib import locked, run

run("uvx", f"ruff@{locked('ruff')}", "check", "--quiet", "--select", "I", "--fix", ".")
