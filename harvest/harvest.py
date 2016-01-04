import time
import requests
import dateutil.parser
import datetime
from base64 import b64encode

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

HARVEST_STATUS_URL = 'http://www.harveststatus.com/api/v2/status.json'


class Error(requests.HTTPError):
    pass


class NotFoundError(Error):
    pass


class UnauthorizedError(Error):
    pass


class Harvest(object):
    def __init__(self, uri, email, password, put_auth_in_header=True):
        parsed = urlparse(uri)
        if not (parsed.scheme and parsed.netloc):
            raise ValueError('Invalid uri "{0}".'.format(uri))
        self.uri = uri
        self.email = email
        self.password = password
        self._headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0',
        }
        if put_auth_in_header:
            key = b64encode('{self.email}:{self.password}'
                            .format(self=self).encode('utf8')).decode('utf8')
            self._headers['Authorization'] = 'Basic {0}'.format(key)

    def status(self):
        return status()

    # Accounts
    def who_am_i(self):
        return self._get('/account/who_am_i')

    # Client Contacts
    def contacts(self, updated_since=None):
        url = '/contacts'
        if updated_since is not None:
            updated_since = _format_date(updated_since)
            url = '{0}?updated_since={1}'.format(url, updated_since)
        return self._get(url)

    def get_contact(self, contact_id):
        return self._get('/contacts/{0}'.format(contact_id))

    def create_contact(self, fname, lname, **kwargs):
        url = '/contacts'
        kwargs.update({'first-name': fname, 'last-name': lname})
        return self._post(url, data=kwargs)

    def client_contacts(self, client_id, updated_since=None):
        url = '/clients/{0}/contacts'.format(client_id)
        if updated_since is not None:
            updated_since = _format_date(updated_since)
            url = '{0}?updated_since={1}'.format(url, updated_since)
        return self._get(url)

    def update_contact(self, contact_id, **kwargs):
        url = '/contacts/{0}'.format(contact_id)
        return self._put(url, data=kwargs)

    def delete_contact(self, contact_id):
        return self._delete('/contacts/{0}'.format(contact_id))

    # Clients
    def clients(self, updated_since=None):
        url = '/clients'
        if updated_since is not None:
            updated_since = _format_date(updated_since)
            url = '{0}?updated_since={1}'.format(url, updated_since)
        return self._get(url)

    def get_client(self, client_id):
        return self._get('/clients/{0}'.format(client_id))

    def create_client(self, name, **kwargs):
        url = '/clients'
        kwargs.update({'name': name})
        return self._post(url, data=kwargs)

    def update_client(self, client_id, **kwargs):
        url = '/clients/{0}'.format(client_id)
        return self._put(url, data=kwargs)

    def toggle_client_active(self, client_id):
        return self._get('/clients/{0}/toggle'.format(client_id))

    def delete_client(self, client_id):
        return self._delete('/clients/{0}'.format(client_id))

    # Projects
    def get_projects(self, client_id=None, updated_since=None):
        url = '/projects'
        if updated_since is not None:
            updated_since = _format_date(updated_since)
            url = '{0}?updated_since={1}'.format(url, updated_since)
        if client_id is not None:
            url = '{0}?client={1}'.format(url, client_id)
        return self._get(url)

    def get_project(self, project_id):
        return self._get('/projects/{0}'.format(project_id))

    def create_project(self, name, **kwargs):
        url = '/projects'
        kwargs.update({'name': name})
        return self._post(url, data=kwargs)

    def update_project(self, project_id, **kwargs):
        url = '/projects/{0}'.format(project_id)
        return self._put(url, data=kwargs)

    def toggle_project_active(self, project_id):
        return self._get('/projects/{0}/toggle'.format(project_id))

    def delete_project(self, project_id):
        return self._delete('/projects/{0}'.format(project_id))

    # Tasks
    def get_tasks(self, client_id=None, updated_since=None):
        url = '/tasks'
        if updated_since is not None:
            updated_since = _format_date(updated_since)
            url = '{0}?updated_since={1}'.format(url, updated_since)
        if client_id is not None:
            url = '{0}?client={1}'.format(url, client_id)
        return self._get(url)

    def get_task(self, task_id):
        return self._get('/tasks/{0}'.format(task_id))

    def create_task(self, name, **kwargs):
        url = '/tasks'
        kwargs.update({'name': name})
        return self._post(url, data=kwargs)

    def update_task(self, task_id, **kwargs):
        url = '/tasks/{0}'.format(task_id)
        return self._put(url, data=kwargs)

    def toggle_task_active(self, task_id):
        return self._get('/tasks/{0}/toggle'.format(task_id))

    def delete_task(self, task_id):
        return self._delete('/tasks/{0}'.format(task_id))

    # Expense Categories
    def get_expense_categories(self):
        return self._get('/expense_categories')

    def create_expense_category(self, **kwargs):
        return self._post('/expense_categories', data=kwargs)

    def update_expense_category(self, expense_category_id, **kwargs):
        return self._put('/expense_categories/{0}'
                         .format(expense_category_id), data=kwargs)

    def get_expense_category(self, expense_category_id):
        return self._get('/expense_categories/{0}'.format(expense_category_id))

    def delete_expense_category(self, expense_category_id):
        return self._delete('/expense_categories/{0}'
                            .format(expense_category_id))

    def toggle_expense_category_active(self, expense_category_id):
        return self._get('/expense_categories/{0}/toggle'
                         .format(expense_category_id))

    # Time Tracking
    def get_today(self):
        return self._get('/daily')

    def get_day(self, date):
        date = _parse_date(date)
        day_of_year = date.timetuple().tm_yday
        return self._get('/daily/{0}/{1}'.format(day_of_year, date.year))

    def get_entry(self, entry_id):
        return self._get('/daily/show/{0}'.format(entry_id))

    def toggle_timer(self, entry_id):
        return self._get('/daily/timer/{0}'.format(entry_id))

    def add(self, data):
        self._format_dates(data, 'spent_at')
        return self._post('/daily/add', data)

    def delete(self, entry_id):
        return self._delete('/daily/delete/{0}'.format(entry_id))

    def update(self, entry_id, data):
        return self._post('/daily/update/{0}'.format(entry_id), data)

    def _get(self, path='/', data=None):
        return self._request('GET', path, data)

    def _post(self, path='/', data=None):
        return self._request('POST', path, data)

    def _put(self, path='/', data=None):
        return self._request('PUT', path, data)

    def _delete(self, path='/', data=None):
        return self._request('DELETE', path, data)

    def _request(self, method='GET', path='/', data=None):
        kwargs = {
            'method': method,
            'url': '{self.uri}{path}'.format(self=self, path=path),
            'headers': self._headers,
            'data': data,
        }
        if 'Authorization' not in self._headers:
            kwargs['auth'] = (self.email, self.password)

        try:
            resp = requests.request(**kwargs)
            resp.raise_for_status()
            if 'DELETE' not in method:
                return resp.json()
            return resp
        except requests.HTTPError as e:
            if resp.status_code == 503:
                # if throttled, try again.
                retry_after = int(resp.headers.get('Retry-After', '15'))
                self._retries = getattr(self, '_retries', 0) + 1
                if self._retries > 5:
                    raise
                print("Harvest is throttling requests, retrying in {} "
                      "seconds...".format(retry_after))
                time.sleep(retry_after)
                return self._request(method, path, data)
            if resp.status_code == 404:
                raise NotFoundError(e, **e.__dict__)
            if resp.status_code == 401:
                raise UnauthorizedError(e, **e.__dict__)
            raise Error(e, **e.__dict__)

    def _format_dates(self, data, *args):
        for arg in args:
            if data.get(arg):
                data[arg] = _format_date(data[arg])


def status():
    try:
        status = requests.get(HARVEST_STATUS_URL).json().get('status', {})
    except:
        status = {}
    return status


def _parse_date(date_input):
    if isinstance(date_input, datetime.date):
        return date_input
    if isinstance(date_input, datetime.datetime):
        return date_input.date()
    return dateutil.parser.parse(date_input).date()


def _format_date(date_input):
    date = _parse_date(date_input)
    return date.strftime('%a, %-d %b %Y')
