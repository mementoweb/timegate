# Memento TimeGate
Make your web resources [Memento](http://www.mementoweb.org) compliant in a few easy steps.

The Memento framework enables datetime negotiation for web resources. Knowing the URI of a Memento-compliant web resource, a user can select a date and see what it was like around that time.


## Introduction

In order to support Memento, a web server must obviously have accessible archives of its online resources. And it must also have a piece of software that handles the datetime negotiation according to the Memento protocol for those resources.

But in such datetime negotiation server, only a small proportion of the code is specific to the particular web resources it handles. The main part of logic will be very similar throughout many implementations.
TimeGate isolates the core components and functionality. With it, there's no need to implement, or to re-implement the same logic and algorithms over and over again.
Its architecture is designed to accept easy-to-code plugins to match any web resources.

From now on, this documentation will refer to the web server where resources and archives are as the **web server** and to the Memento TimeGate datetime negotiation server as the **TimeGate**.

* Suppose you have a web resource accessible in a web server by some URI. We call the resource the **Original Resource** and refer to its URI as **URI-R**.
* Suppose a web server has a snapshot of what this URI-R looked like in the past. We call such a snapshot a **Memento** and we refer to its URI as **URI-M**. There could be many snapshots of URI-R, taken at different moments in time, each Memento i with its distinct URI-Mi.
The Mementos do not necessary need to be in the same web server as the Original Resources.


## Example
![Image](https://raw.githubusercontent.com/mementoweb/timegate/master/doc/uris_example.png)

There are only two steps to make such resource Memento compliant.

## Step 1: Setting up TimeGate
The first thing to do is to set up the TimeGate for the specific web server.
* Run the TimeGate with your custom handler. The handler is the piece of code that is specific to how the web server manages Original Resources and Mementos. It needs to implement either one of the following:
  - Given a URI-R, return the list of URI-Ms along with their respective dates.
  - Given a URI-R and a datetime, return one single URI-M along with its date.

## Step 2: Providing the headers
The second thing to do is to provide Memento's HTTP headers at the web server.
* Add HTTP headers required by the Memento protocol to responses from the Original Resource and its Mementos:
  - For the Original Resource, add a "Link" header that points at its TimeGate
  - For each Memento, add a "Link" header that points at the TimeGate
  - For each Memento, add a "Link" header that points to the Original Resource
  - For each Memento, add a Memento-Datetime header that conveys the snapshot datetime

Using the previous example, and supposing a TimeGate is running at `http://example.com/timegate/`, Memento HTTP response headers for the Original Resource and one Memento look as follows.
![Image](https://raw.githubusercontent.com/mementoweb/timegate/master/doc/headers_example.png)

And that's it! With the TimeGate, datetime negotiation is now possible for these resources.

## How it works
Read the [big picture](https://github.com/mementoweb/timegate/wiki/The-Big-Picture) to understand how it works and what are the requirements.

## Getting Started
Start by [reading the guide](https://github.com/mementoweb/timegate/wiki/Getting-Started) for comprehensive information about how to use TimeGate for your own web resources.

## Requirements
* [Python](https://www.python.org)
* [uWSGI](http://uwsgi-docs.readthedocs.org/en/latest/)

## Documentation
See the [wiki](https://github.com/mementoweb/timegate/wiki).

## License
See the [LICENSE](https://github.com/mementoweb/timegate/blob/master/LICENSE) file.
