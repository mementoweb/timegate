# Memento TimeGate

TimeGate is a [WSGI](http://wsgi.readthedocs.org/en/latest/) server allows simple implementation of [Memento](http://mementoweb.org) TimeGate capabilities for a web resource having a version API.
TimeGate is a generic server that sits between a Memento client and any type of resource version API to enable easy implementation Datetime negotiation for the resources.
The server manages all the content negotiation logic, from request processing, best memento query and selection to response headers creation.


## Architecture

![architecture]
(https://raw.githubusercontent.com/mementoweb/timegate/master/architecture.png)

The system can be seen as three components.

- The Memento user who wishes to retrieve an older version of a resource
- The entity where the active version (original URI) and revisions (mementos) can be accessed. This entity must provide a version access API.
- The TimeGate which itself is composed of two main elements:
  - One API-specific handler
  - The generic TimeGate code

## Handler

A Handler is an API-specific piece of code that plugs into the TimeGate to match any kind of API.
The handlers are kept as simple as possible. They require to have only the following:

- It must be the unique python class defined in `core/extensions/`. To use several handlers, see #
- Implement the `getall(self, uri_r)` function. This function is called by the TimeGate to retrieve the history an original resource `uri_r`.
The return value must be a list of pairs: `[(uri_m1, date1), (uri_m2, date2), ...]` . Each pair `(uri_m, date)` contains the URI of an archived version of R `uri_m`, and the date at which it was archived `date`.
All URI fields must be strings
All Date fields must be strings formatted as the ISO, date format
- If the API cannot return the entire history for a resource, the handler must implement the `getone(self, uri_r, date)` function. This function will be called by the TimeGate to retrieve the best Memento for `uri_` at the date `date`. The function is the same as `getall()` except that the return value will contain only one pair: `[(uri_m, date)]` which is the best memento that the handler could provide taking into account the limits of the API.
- For simplicity, a handler can extend the `Handler` base-class.

Handlers examples are provided for several APIs:
- [GitHub.com](https://developer.github.com/v3/)
- [arXiv.org](http://arxiv.org/help/oa/index)
- [wikipedia.org](https://www.wikipedia.org)
- [awoiaf.westeros.org](http://awoiaf.westeros.org/index.php/Main_Page)

## Running and stopping the server
To start it, there are two possibilities:
- Either execute`uwsgi --http :PORT --wsgi-file application.py --master [--pidfile /path/to/file.pid]`
- Or edit the uWSGI configuration in conf/timegate.ini and then execute `uwsgi conf/timegate.ini`

To stop the server:
- Simply use `CTRL+C` if it is running in foreground.
- To use the server in background, store the pid in a file and stop it using `uwsgi --stop /path/to/file.pid`.

## Configuring the server
Config file: `conf/config.cfg`
- `host` The server's base URI
- `strict_datetime` When False, the server will try to parse Accept-Datetime header values that do not comply with the RFC
- `single` When False, only one handler will be run by the TimeGate. To use multiple handlers, see multiple handlers
- `is_vcs` When True, the resource is considered complete, thus the best memento for a date D will be the closest *before* D. When False, the history is considered to be snapshots, thus the best memento is the *absolute* closest to the requested date.
- `activated` When True, the cache is used else, all cache will be misses.
- `expiration_seconds` Time, in seconds, before a cache entry is removed (space parameter)
- `tolerance_seconds` Time in seconds, before the server considers that the history might have changed (precision parameter).
- `fdata` Path to the cache data file
- `flock` Path to the cache lock file
- `fdogpile` Path to the cache dogpile

