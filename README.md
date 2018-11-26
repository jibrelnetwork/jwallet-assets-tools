jwallet-assets-tools
===

Jwallet assets validator and other tools.


Install
---

Installing from github:

```bash
pip install -e git+git@github.com:jibrelnetwork/jwallet-assets-tools.git#egg=jwallet-assets-tools
```


Usage
---

`jwallet-assets-tools` provides a command with same name. Example of `assets.json` validation 
over mainnet node and with progress bar displayed (also this command suitable for CI):

```bash
jwallet-assets-tools validate assets.json --node=https://main-node.jwallet.network/ --progress
```

Other options available:

```bash
jwallet-assets-tools --help
jwallet-assets-tools validate --help
```

Fast validation (must be used as pre-commit hook when contributing to `jwallet-assets` repo), log only on error:

```bash
jwallet-assets-tools validate assets.json --node=https://main-node.jwallet.network/ --loglevel=ERROR
```
