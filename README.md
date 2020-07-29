# dirwatch

Watches a directory and runs a command whenever it is updated.

The intention is that it can be used to run an `rsync` command to back the
directory up to a remote location.

Example:

```shell script
dirwatch /watched_dir rsync -r /watched_dir dest:/target_dir
```
