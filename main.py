from pathlib import Path
import os
import argparse
import logging
from git import Repo
import anthropic

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def main(push=False):
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
        logger.info(".shitty_auto_vcs file either not found or not valid")
        exit(1)

    os.chdir(remote_base_file.parent)

    repo = Repo(".")

    if not repo.is_dirty(untracked_files=True):
        logger.info("No changes to commit.")
        exit(0)

    logger.debug("Staging all changes...")
    repo.git.add(all=True)

    diff_output = repo.git.diff('HEAD', '--histogram')

    logger.debug("Generating commit message using AI...")
    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-3-5-sonnet-latest",
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
    commit_message = message.content[0].text.strip()

    logger.info(f"Commit message: {commit_message}")
    repo.git.commit('-m', commit_message)
    logger.debug("Changes committed successfully.")

    if push:
        logger.debug("Pushing to remote repository...")
        repo.git.push()
        logger.debug("Changes pushed successfully.")
        logger.info("Changes pushed to remote repository.")
    else:
        logger.info("Skipping push (use --push to push changes).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-generate commit messages and commit changes")
    parser.add_argument("--push", action="store_true", help="Push changes to remote repository after committing")

    args = parser.parse_args()
    main(push=args.push)