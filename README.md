# Memento TimeGate
Make your website [Memento](http://www.mementoweb.org) compliant with a few easy steps.

The Memento protocol enables date time negotiation for web resources. With it, a user can see what a resource was in a certain point in the past.

* Suppose you have a resource (typically a web page) located at some URI. We call it the original URI (or URI-R).
* And suppose you have dated archives (or Mementos) of what this URI-R returned in the past. Each version i is accessible through its specific URI (we call it URI-Mi).

[Image]()

With this setup, there are two steps to make those resources Memento compliant.
* Install the TimeGate server and implement your custom handler. This handler is specific to your website and needs only to return the list of dated mementos URI-Ms given an original resource URI-R, or return a single best Memento URI-M given an original resource URI-R and a date time.
* Append the required Memento HTTP headers to the current ones. The mandatory headers are links to the TimeGate from original resources and Mementos. And additionally, Mementos need to advertise their dates using a `Memento-Datetime:` header.


A handler is a python file that will typically talk to an API to get the list of archives, along with their dates, and return it to the TimeGate. If no API is present, it is possible to use page scraping or even data-base queries. Anything will do. All the logic of the Memento date time negotiation is then done by the TimeGate.

## Getting Started
Start by [reading the guide](https://github.com/mementoweb/timegate/wiki/Getting-Started) for comprehensive information about the TimeGate server.

## Requirements
* [Python](https://www.python.org)
* [uWSGI](http://uwsgi-docs.readthedocs.org/en/latest/) 

## License
See the [LICENSE](https://github.com/mementoweb/timegate/blob/master/LICENSE) file.


