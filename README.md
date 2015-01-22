imago
=====

This is the django app that powers api.opencivicdata.org

Python 3.3 or newer required, Python 2 compatibility is not guaranteed.

Getting Started
===============

* [Install Represent Boundaries](http://represent.poplus.org/docs/install/).
* Add `'imago'` to your `INSTALLED_APPS`.
* Add `('', include('imago.urls')),` to `urls.py`.
* Set `IMAGO_COUNTRY` to a two-letter, lowercase country code like `'us'` in `settings.py`, to select which country's [Open Civic Data Division Identifiers](http://docs.opencivicdata.org/en/latest/proposals/0002.html) to use.
* Set `IMAGO_BOUNDARY_MAPPINGS` in `settings.py`, a dictionary in which each key is the slug of a boundary set and each value is a dictionary, which has as keys:
  * `key`: The property of a division identifier that will be used to match a boundary's `external_id`.
  * `prefix`: Imago will prepend this prefix to a boundary's `external_id`, and will look for a division identifier whose property, identified by `key`, matches.
  * `ignore`: Either `None` or a regular expression string. If no match is found, and if either `ignore` is `None` or the boundary name doesn't match the regular expression, a warning will be issued about the unmatched `external_id`.
  * `start`: Ignored. This functionality has been moved into [Represent Boundaries](http://represent.poplus.org/).

See [api.opencivicdata.org's `settings.py`](https://github.com/opencivicdata/api.opencivicdata.org/blob/master/ocdapi/settings.py#L132) for an example.
