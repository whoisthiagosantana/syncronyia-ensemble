# Upstream provenance and fork boundaries

Fork: [whoisthiagosantana/syncronyia-ensemble](https://github.com/whoisthiagosantana/syncronyia-ensemble).
Upstream: [FoundationAgents/MetaGPT](https://github.com/FoundationAgents/MetaGPT).
Baseline: `11cdf466d042aece04fc6cfd13b28e1a70341b1f`.
Upstream commit date: 2026-01-21T18:12:32+08:00.
Initial assessment/fork date: 2026-11-05.

Syncronyia Ensemble is a provisional experimental fork identity. Name/trademark/domain
availability has not been established. It does not imply endorsement by the upstream
authors, Anthropic, or OpenAI.

## Initial write surface

The initial change adds the fork README, preserves the original as `README.upstream.md`,
adds this documentation set and agent guidance, and excludes `.local/` private working
notes from Git. It does not rename the Python package, change runtime code/dependencies,
install services, register workers, add credentials, deploy, or migrate company records.

The upstream [MIT license](../../LICENSE) and attribution are preserved. The upstream README
describes upstream functionality; it is not a promise of subscription-only or governed
operation in this experimental fork. Unchanged upstream examples may call paid APIs or
invoke executable tools and are not the experiment's approved execution path.

## Repository operation

GitHub Actions is disabled for the initial research fork so inherited workflows are not
mistaken for verified fork controls or launched by documentation pushes. Re-enabling CI
requires reviewing workflow credentials, triggers and the actual checks for the scoped work.
This setting does not disable runtime tools in MetaGPT: there is no runtime capability
enforcement implementation in the initial fork.

Maintain `upstream` for source provenance and `origin` for this fork. Update the baseline
and recheck source findings before accepting an upstream merge. Keep source claims pinned
to a commit. Do not automatically merge a moving upstream branch into an active experiment.

The public documentation contains shareable code assessment and proposed integration
contracts. Private environment inventories and pilot evidence remain outside published Git
history. Local ignored notes are retained for the owner's inspection but are not versioned
or portable acceptance evidence.

## Validation boundaries

For the initial documentation delivery: verify the GitHub fork/parent identity, upstream
ancestry, original README and license preservation, local documentation links, explicit
changed-file scope, absence of private environment material, and disabled Actions setting.
No runtime suite or model generation is warranted by documentation-only edits. These
checks do not prove native auth, MCP functionality, security isolation or productivity.
The preserved upstream README contains seven existing trailing-whitespace lines. Keep
that file byte-identical and exclude it from new-prose whitespace checks; verify its bytes
against the upstream Git object instead.

Roll back the documentation change with `git revert` of its commit, preserving the fork and
upstream history. No branch, backup, volume or company data needs deletion.
