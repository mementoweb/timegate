# Memento TimeGate
Make your web resources [Memento](http://www.mementoweb.org) compliant in a few easy steps.

TimeGate allows simple implementation of Memento capabilities for web resources having accessible revisions.
The Memento framework enables date time negotiation for web resources. With it, a user can see what a resource was in a certain point in the past.
* Suppose you have a web resource identified by some URI. We call the resource the **Original Resource** and refer to its URI as **URI-R**.
* Suppose you have a snapshot of what this URI-R looked like in the past. We call such a snapshot a **Memento** and we refer to its URI as **URI-M**. There could be many snapshots of URI-R, taken at different moments in time, each with their distinct URI-Mi.

Example
![Image](https://raw.githubusercontent.com/mementoweb/timegate/master/doc/uris_example.png)

With this setup, there are two steps to make such web resources Memento compliant.
* Run the TimeGate with your custom handler. The handler is the piece of code that is specific to the resources. It needs to implement either one of the following:
  - Given a URI-R, return the list of URI-Ms along with their respective dates.
  - Given a URI-R and a date time, return one single URI-M along with its date.
* Add HTTP headers required by the Memento protocol to responses from the Original Resource and its Mementos:
  - For the Original Resource, add a "Link" header that points at its TimeGate
  - For each Memento, add a "Link" header that points at the TimeGate
  - For each Memento, add a "Link" header that points to the Original Resource
  - For each Memento, add a Memento-Datetime header that conveys the snapshot datetime

Using the previous example, and supposing a TimeGate is running at `http://example.com/timegate/`, Memento HTTP response headers for the Original Resource and one Memento look as follows.
![Image](https://raw.githubusercontent.com/mementoweb/timegate/master/doc/headers_example.png)

And that's it! With the TimeGate, date time negotiation is now possible for this resource.

## How it works
Read the [big picture](https://github.com/mementoweb/timegate/wiki/The-Big-Picture) to understand how it works.

## Getting Started
Start by [reading the guide](https://github.com/mementoweb/timegate/wiki/Getting-Started) for comprehensive information about TimeGate.

## Requirements
* [Python](https://www.python.org)
* [uWSGI](http://uwsgi-docs.readthedocs.org/en/latest/)

## Documentation
See the [wiki](https://github.com/mementoweb/timegate/wiki).

## License
See the [LICENSE](https://github.com/mementoweb/timegate/blob/master/LICENSE) file.
