# fastapi-synchronous-sqlalchemy

A repo to check some of my assumptions about fastapi + synchronous sqlalchemy connections.

## what

We run the code from fastapi's documentation https://fastapi.tiangolo.com/tutorial/sql-databases/
and load test it with a simple client. See `app.py` and `client.py`.

## why

With as little as 100 connections the endpoints begin returning 500 errors
due to SQLAlchemy queue timeouts. To see this run the following:

```bash
docker compose build
docker compose up
```

and in a separate shell run

```python
python -m venv venv
source venv/bin/activate
pip install -e .
python client.py http://localhost:8000 100
```

This hits the example code from the fastapi docs with 100 concurrent requests.

## root cause

This seems to be due to the way fastapi handles the creation / teardown of
the session dependency. Specifcally requests waiting for a database connection
exhaust the anyio threadpool, whereas requests that hold database connections
can't run the code to discard the connection since a thread is not available
to call the dependency teardown.

This manifests in an immediate 30s hang followed by a slew of 500s and completed
requests.

## remediations

If we move the database session handling out of a dependency it can suddenly handle
bursts of 1000+ concurrent requests without errors. You can try this
by running the client against http://localhost:9000, which hits the alternative
app in `app_alternative.py`.

In fact, running the client against the two variants of the app we get:

```bash
$ python client.py http://localhost:8000 100
<snip>
100 requests finished in 91.33 seconds
    encountered 117 errors

$ python client.py http://localhost:9000 1000
<snip>
1000 requests finished in 8.57 seconds
    encountered 0 errors
```

## thoughts and recomendations

For the moment the conclusion seems to be: don't use dependencies for SQLAlchemy syncronous session management.
The problem is also present if handling the session in middlewares.

Some alternatives:
- manually manage the session in every endpoint
- use async SQLAlchemy if you are able to
- monkeypatch fastapi.routing.run_endpoint_function to manage a db session in the same thread the endpoint runs in*

*maybe I'll expand on this at some point in future
