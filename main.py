from pathlib import Path
import os
from git import Repo
import anthropic

def main():
    # anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    cwd = Path()
    parent: Path = Path(os.getcwd())
    remote_base_file = Path()
    shitty_auto_vcs = False
    while cwd != parent:
        cwd = parent
        parent = cwd.parent
        if (remote_base_file := (cwd / ".shitty_auto_vcs")).is_file():
            shitty_auto_vcs = True
            break
    if not shitty_auto_vcs:
        raise (ValueError(".shitty_auto_vcs file either not found or not valid"))

    os.chdir(remote_base_file.parent)

    repo = Repo(".")

    if not repo.is_dirty(untracked_files=True):
        print("No changes to commit.")
        exit(0)

    repo.git.add(all=True)

    diff_output = repo.git.diff('HEAD', '--histogram')

    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-sonnet-4-0",
        max_tokens=1000,
        temperature=1,
        system="Analyze this diff, write a commit message based on this diff, STRICTLY following the following format:\n"
               "```"
               "Commit Name\n"
               "Commit description"
               "```"
               "with Commit Name being roughly in a 50-80 symbols range, and Commit Description being in 70-100 symbols range, being separated by a single newline."
               "Just output Commit Name and Commit Description, without any other text, without anything like \"Sure, here's your commit message!\"."
               "Feel free to make it shorter if there's not much changes, or make it slightly bit longer if there's a lot of changes, but try to keep it concise either way.",
        messages=[
            anthropic.types.MessageParam(
                role="user",
                content=diff_output
            )
        ]
    )
    commit_message = message.content[0].text

    commit_message = commit_message
    repo.git.commit('-m', commit_message)

    repo.git.push()


if __name__ == "__main__":
    main()