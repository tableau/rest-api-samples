

import requests
from rest_api_utils import _check_status

def main():
  data ={"text":"Coming soon - gitlab notifications!"}
  url = "https://hooks.slack.com/services/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"

  print data
  response = requests.put(url, json=data)
  _check_status(response, 200)

if __name__ == "__main__":
    main()

