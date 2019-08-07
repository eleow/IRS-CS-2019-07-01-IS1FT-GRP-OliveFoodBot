from urllib.parse import quote
import requests
import pprint


# Using Yelp API v3
YELP_API_KEY = "rG5TOrDyCq0G-lIelg9XzKfBcSNrc2F7zsa3C99Nray3q_-Wz8YU1Jdi1rAu7-gSQwdKCuZA0b9GXCp5xMImW9_dxQo_9ib4OAJ-PXRyqPGakfQD8WHL8BX7uDNJXXYx"
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'

# Defaults
SEARCH_LIMIT = 5
DEBUG_MODE = False

def yelp_request(host, path, api_key, url_params={}, debug=DEBUG_MODE):
    """Given API_KEY, send a GET request to the Yelp REST API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        API_KEY (str): Your API Key.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {'Authorization': 'Bearer %s' % api_key}
    if (debug): print(u'Querying {0} ...'.format(url))

    response = requests.request('GET', url, headers=headers, params=url_params)
    if (response.headers.get("RateLimit-Remaining") == '0'):
        print("Oops.. We have exceeded Yelp Fusion API daily access limit... Please try again tomorrow!")
    return response.json()


def yelp_search(api_key, term, location, debug):
    """Query Yelp Search API by a search term and location.
    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.
    Returns:
        dict: The JSON response from the request.
    """
    url_params = {'term': term.replace(
        ' ', '+'), 'location': location.replace(' ', '+'), 'limit': SEARCH_LIMIT}
    return yelp_request(API_HOST, SEARCH_PATH, api_key, url_params=url_params, debug=debug)


def yelp_business(api_key, business_id, debug=DEBUG_MODE):
    """Query Yelp Business API by a business ID.
    Args:
        business_id (str): The ID of the business to query.
    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id
    return yelp_request(API_HOST, business_path, api_key, debug)


def yelp_query_api(term, location, debug=DEBUG_MODE, num_results=1):
    """Queries the API by the input values from the user.
    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.`
    Returns:
        array of responses that match num_results
    """
    # Check if this business exists. If exists, we get its ID
    response = yelp_search(YELP_API_KEY, term, location, debug)
    businesses = response.get('businesses')

    if not businesses:
        print(u'No businesses for {0} in {1} found.'.format(term, location))
        return None


    # If exists, then we get its details
    num_results = min(len(businesses), num_results)
    print(u'{0} businesses found, querying business info ' \
        'for the top {1} results ...'.format(
            len(businesses), num_results))

    responseArr = []
    for b in businesses[:num_results]:
        business_id = b['id']
        responseArr.append(yelp_business(YELP_API_KEY, business_id))

        if (debug):
            print(u'Result for business "{0}" found:'.format(business_id))
            pprint.pprint(response, indent=2)

    return responseArr
