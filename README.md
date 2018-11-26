jwallet-assets
===

Repository with assets metadata used by jwallet application.


Assets file format
---

There are `assets.json` files which format described in [assets.schema.json].

Asset root keys:

- `name` — asset name in apps
- `symbol` — asset symbol to show in apps
- `blockchainParams` — technical, network-related parameters (required only for type=erc-20)
- `display` — asset visualization parameters
- `assetPage` — content section (optional)

`blockchainParams` keys:

- `type` — asset type (`erc-20`, `ethereum`)
- `features` — additional ERC-20 features list (only `mintable` available for a while; optional)
- `address` — contract address (required only for `type=erc-20`)
- `staticGasAmount` — maximum gas amount used in contract transactions
- `deploymentBlockNumber` — contract deployment block number 
(it is a first transaction block for a while, not real deployment; see [JSEARCH-49])
— `decimals` — number of digits after decimal point to display value

`display` keys:

- `isDefaultForcedDisplay` — show this asset in wallet by default
- `digitalAssetsListPriority` — order index in assets list

`assetPage` keys:

- `description`
- `urls` — list of links related to this asset


CI make commands
---

`make validate` — full validation (about 1.5 - 2 hours to complete)
`make lint` — `validate-fast` alias
`make test` — run tests (pytest)


Contributing
---

If you want to change data in this repository you must validate your data 
before pushing to repository. Before you can use validator you must install 
its dependencies from `requirements.txt` (it would be better to use virtualenv 
or virtualenvwrapper):

```bash
pip install -r requirements.txt
``` 

You can install pre-commit hook to validate assets data with:

```bash
make hooks
``` 

So if validation failed changes will be not committed. If you want to bypass 
validation, just commit with `-n` option:

```bash
git commit -n
```

You can also invoke validation manually:

```bash
make pre-commit
```

or

```bash
python -m tools validate <assets_json> --fast --node="<ethereum_node_url"
```

For a **full validation** with progress bar (around 2hr required for full check):

```bash
make validate
```

```bash
python -m tools validate <assets_json> --progress --node="<ethereum_node_url>"
```

more options available, see

```bash
python -m tools validate --help
```

[assets.schema.json]: https://github.com/jibrelnetwork/jwallet-assets/blob/master/tools/assets.schema.json

[JSEARCH-49]: https://jibrelnetwork.atlassian.net/browse/JSEARCH-49
