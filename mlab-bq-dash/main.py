import logging
import os

from oauth2client.appengine import oauth2decorator_from_clientsecrets
import webapp2

import bqclient
import gviz_data_table as charts

from google.appengine.api import memcache
from google.appengine.ext.webapp.template import render


CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')
SCOPES = [
    'https://www.googleapis.com/auth/bigquery'
]
decorator = oauth2decorator_from_clientsecrets(
    filename=CLIENT_SECRETS,
    scope=SCOPES,
    cache=memcache)

# Project ID for a project where you and your users
# are viewing members.  This is where the bill will be sent.
# During the limited availability preview, there is no bill.
# Replace this value with the Client ID value from your project,
# the same numeric value you used in client_secrets.json
BILLING_PROJECT_ID = "294885104230"
DATA_PROJECT_ID = "publicdata"
DATASET = "samples"
TABLE = "natality"
QUERY = ("select state,"
         "SUM(gestation_weeks) / COUNT(gestation_weeks) as weeks "
         "from %s:%s.%s "
         "where year > 1990 and year < 2005 "
         "and IS_EXPLICITLY_DEFINED(gestation_weeks) "
         "group by state order by weeks") % (DATA_PROJECT_ID, DATASET, TABLE)
MLAB_QUERY = (
"""
SELECT
    STRFTIME_UTC_USEC(web100_log_entry.log_time * 1000000, '%Y-%m-01') AS month,
    COUNT(IF(connection_spec.data_direction == 0, 1, NULL)) AS upload_tests,
    COUNT(IF(connection_spec.data_direction == 1, 1, NULL)) AS download_tests,
FROM
    plx.google:m_lab.ndt.all
WHERE
    web100_log_entry.log_time * 1000000 > PARSE_UTC_USEC("2010-01-01 00:00:00")
GROUP BY
    month
ORDER BY
    month ASC
""")
MLAB_QUERY_DAILY = (
"""
SELECT
    STRFTIME_UTC_USEC(web100_log_entry.log_time * 1000000, '%m-%d') AS day,
    COUNT(IF(connection_spec.data_direction == 0, 1, NULL)) AS upload_tests,
    COUNT(IF(connection_spec.data_direction == 1, 1, NULL)) AS download_tests,
FROM
    plx.google:m_lab.ndt.all
WHERE
    web100_log_entry.log_time * 1000000 > PARSE_UTC_USEC("2016-07-01 00:00:00")
GROUP BY
    day
ORDER BY
    day ASC
""")
# resolution: hours, days, months.
# duration: a few days, a few months, a few years.
# start time: 
# upload / download 
# different protocols
# different clients
# different country
# different sites
mem = memcache.Client()


class MainPage(webapp2.RequestHandler):
    # [START bq2geo]
    def _bq2geo(self, bqdata):
        # geodata output for region maps must be in the format region, value.
        # Assume the query output is in this format, get names from schema.
        logging.info(bqdata)
        logging.info("START CONVERSION ---")
        table = charts.Table()
        months = bqdata["schema"]["fields"][0]["name"]
        uploads = bqdata["schema"]["fields"][1]["name"]
        downloads = bqdata["schema"]["fields"][2]["name"]
        table.add_column("", unicode, "Months")
        table.add_column(uploads, float, uploads)
        table.add_column(downloads, float, downloads)
        for row in bqdata["rows"]:
            table.append([row["f"][0]["v"], float(row["f"][1]["v"]), float(row["f"][2]["v"])])
        logging.info("FINISHED CONVERSION ---")
        logging.info(table)
        return charts.encode(table)
    # [END bq2geo]
    
    @decorator.oauth_required
    def get(self):
        #data = mem.get('mlab')
        if True:
            bq = bqclient.BigQueryClient(decorator)
            logging.info("START QUERY ---")
            values = self._bq2geo(bq.Query(MLAB_QUERY_DAILY, BILLING_PROJECT_ID))
            data = {'data': values,
                    'query': MLAB_QUERY}
            mem.set('mlab', data)
        template = os.path.join(os.path.dirname(__file__), 'index-table.html')
        self.response.out.write(render(template, data))

application = webapp2.WSGIApplication([
    ('/', MainPage),
    (decorator.callback_path, decorator.callback_handler())
], debug=True)
