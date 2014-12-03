# Memento TimeGate

TimeGate is a [WSGI](http://wsgi.readthedocs.org/en/latest/) server allows simple implementation of [Memento](http://mementoweb.org) TimeGate capabilities for a web resource having a version API.
TimeGate is a generic server that sits between a Memento client and any type of resource version API to enable easy implementation Datetime negotiation for the resources.
The server manages all the content negotiation logic, from request processing, best memento query and selection to response headers creation.


## Architecture

![architecture]
(https://raw.githubusercontent.com/mementoweb/timegate/master/doc/architecture.png)

The system can be seen as three components.

- The Memento user who wishes to retrieve an older version of a resource
- The entity where the active version (original URI) and revisions (mementos) can be accessed. This entity must provide a version access API.
- The TimeGate which itself is composed of two main elements:
  - One API-specific handler
  - The generic TimeGate code

## Handler

![code_architecture]
(https://raw.githubusercontent.com/mementoweb/timegate/master/doc/code_architecture.png)

A Handler is an API-specific piece of code that plugs into the TimeGate to match any kind of API.
The handlers are kept as simple as possible. They require to have only the following:

- A handler must extend the `Handler` base-class, and it must be the only python class to do so.
- Implement the `get_all_mementos(self, uri_r)` function. This function is called by the TimeGate to retrieve the history an original resource `uri_r`.
The return value must be a list of pairs: `[(uri_m1, date1), (uri_m2, date2), ...]` . Each pair `(uri_m, date)` contains the URI of an archived version of R `uri_m`, and the date at which it was archived `date`.
All URI fields must be strings
All Date fields must be strings formatted as the ISO, date format
- If the API cannot return the entire history for a resource, the handler must implement the `get_memento(self, uri_r, date)` function. This function will be called by the TimeGate to retrieve the best Memento for `uri_` at the date `date`.
In this case, the return value will contain only one pair: `(uri_m, date)` which is the best memento that the handler could provide taking into account the limits of the API.


Handlers examples are provided for several APIs:
- [GitHub.com](https://developer.github.com/v3/)
- [arXiv.org](http://arxiv.org/help/oa/index)
- [wikipedia.org](https://www.wikipedia.org)
- [awoiaf.westeros.org](http://awoiaf.westeros.org/index.php/Main_Page)

Other scraping Handlers examples are provided for resources without any API.

## Running and stopping the server
To start it, there are two possibilities:
- Either execute`uwsgi --http :PORT --wsgi-file core/application.py --master [--pidfile /path/to/file.pid]`
- Or edit the uWSGI configuration in conf/timegate.ini and then execute `uwsgi conf/timegate.ini`

To stop the server:
- Simply use `CTRL+C` if it is running in foreground.
- To use the server in background, store the pid in a file and stop it using `uwsgi --stop /path/to/file.pid`.

## Configuring the server
Config file: `conf/config.ini`
- `host` The server's base URI
- `strict_datetime` When `false`, the server will try to parse Accept-Datetime header values that do not comply with the RFC
- `api_time_out` Time, in seconds, before a request to an API times out. Default 5 seconds
- `is_vcs` When `true`, the resource is considered complete, thus the best memento for a date D will be the closest *before* D. When `false`, the history is considered to be snapshots, thus the best memento is the *absolute* closest to the requested date.
- `base_uri` (Optional) String that will be prepended to requested URI if missing. This can be used to shorten the request URI and to avoid repeating the base URI that is common to all resources. For example using `base_uri = http://` or `base_uri = https://example.com/long/path/to/all/resources/`.
- `activated` When `true`, the cache stores TimeMap (from APIs that allows batch `get_all_mementos` requests. When false the cache files are not created.
- `refresh_time` Time in seconds, for which it is assumed that a TimeMap didn't change. Any TimeGate request for a datetime past this period (or any TimeMap request past this period) will trigger a refresh of the cached value. Default 3600 seconds
- `cache_directory` Relative path for data and lock files
- `cache_max_size` The maximum size of the cache directory, in MB. The cache will start deleting values before this limit is reached.


