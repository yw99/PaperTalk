# PaperTalk

PaperTalk is a Codex skill for understanding research papers through evidence-grounded **Author**, **Reviewer**, **Researcher**, and interactive **Panel** perspectives. It focuses on why research choices were made, how well the claims hold up, and what alternative directions may be worth exploring.

## Installation

### Use it inside this repository

Clone the repository and open it in Codex:

```bash
git clone https://github.com/yw99/PaperTalk.git
cd PaperTalk
codex
```

The repository includes `.agents/skills/papertalk`, so Codex can discover the skill when launched from the repository or one of its subdirectories. If it does not appear immediately, restart Codex. See the [official Codex skills documentation](https://developers.openai.com/codex/skills/) for skill discovery details.

### Install it for use in other repositories

Ask Codex's built-in skill installer to install the PaperTalk skill directory:

```text
$skill-installer Install papertalk from https://github.com/yw99/PaperTalk/tree/main/skills/papertalk
```

The skill should be available on the next turn. Restart Codex if it is not detected.

## Example usage

Start with the fixed command reference:

```text
$papertalk help
```

Register and inspect a paper:

```text
$papertalk add <alias> <public_link>
$papertalk list
$papertalk use @<alias>
```

Discuss it from different perspectives:

```text
$papertalk author @<alias> summarize <paper_aspect>
$papertalk reviewer @<alias> critique <claim_or_theorem>
$papertalk researcher @<alias> extend <method_or_open_question>
```

Start and continue an interactive Panel:

```text
$papertalk panel @<alias> <discussion_topic>
$papertalk panel_continue @<alias> reviewer:author <focus_guidance>
```

`panel_continue` always targets the latest Panel for the named paper. The pair `reviewer:author` means that Reviewer responds to Author's newest frozen answer.

## Local state

Registered papers, derived evidence, and Panel sessions are stored under `.papertalk/`. This directory is ignored by Git, so each user keeps an independent local PaperTalk workspace.
