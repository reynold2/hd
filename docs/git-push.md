# Git Push Notes

This repository pushes to:

```text
git@github.com:reynold2/hd.git
```

## Local SSH Key

GitHub uses a repository deploy key for write access:

```text
C:/Users/yukai/.ssh/hd_deploy_ed25519
```

The repository local Git config should contain:

```powershell
git config --local core.sshCommand "ssh -i C:/Users/yukai/.ssh/hd_deploy_ed25519 -o IdentitiesOnly=yes"
```

This makes normal `git push` use the correct key without setting `GIT_SSH_COMMAND` each time.

## Normal Push Flow

```powershell
git status --short --branch
git add <changed-files>
git commit -m "commit message"
git push
```

## If Push Says Deploy Key Denied

Check the local SSH command:

```powershell
git config --local --get core.sshCommand
```

It should print:

```text
ssh -i C:/Users/yukai/.ssh/hd_deploy_ed25519 -o IdentitiesOnly=yes
```

If GitHub says `Key is already in use`, do not reuse `id_ed25519.pub` as a deploy key. Generate a repository-specific key and add the `.pub` content in GitHub repository settings:

```powershell
ssh-keygen -t ed25519 -C "reynold2-hd-deploy" -f $env:USERPROFILE\.ssh\hd_deploy_ed25519 -N ""
Get-Content $env:USERPROFILE\.ssh\hd_deploy_ed25519.pub
```

In GitHub, go to `Settings -> Deploy keys -> Add deploy key`, paste the public key, and enable `Allow write access`.
