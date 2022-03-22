# bluesky-queueserver

Follow the
[tutorial](https://blueskyproject.io/bluesky-queueserver/tutorial.html#running-re-manager-with-custom-startup-code)

Need these two files to start the server and load the instrument:

- `user_group_permissions.yaml` copied from the example
- `starter.py` loads the instrument (the **only** `.py` file in this directory)

- [bluesky-queueserver](#bluesky-queueserver)
  - [Initial test of the server](#initial-test-of-the-server)
    - [run server in a console](#run-server-in-a-console)
    - [Tell qserver to open an environment (in different console)](#tell-qserver-to-open-an-environment-in-different-console)
    - [New output in first console](#new-output-in-first-console)

## Initial test of the server

Starting from a local repository clone (in the root directory of the clone):

### run server in a console

```bash
cd ./qserver
conda activate queue_server
start-re-manager --startup-dir ./
```

### Tell qserver to open an environment (in different console)

```bash
cd ./qserver
conda activate queue_server
qserver environment open
```

### New output in first console

Check for new output in the console where  `start-re-manager` is running.
