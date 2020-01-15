# NEAR | Diagnostic Tool

Save and process programmatically diagnostics exposed by NEAR nodes.

## Steps

### Run your node in diagnostic mode

Add `diagnostic=trace` to `RUST_LOG`.

```bash
export RUST_LOG=diagnostic=trace
```

Run near binary and dump logs to a file.

```bash
cd path/to/nearcore
mkdir ~/.near
cargo run -p near -- run | tee ~/near/node.log
```

### Start log watcher

Install docker

```bash
python3 -m pip install -r requirements.txt
./cli.py --watch ~/near/node.log
```

When run for first time it will pull mongo docker image.

Use `./cli.py --help` to see further options.

