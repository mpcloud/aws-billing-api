'''
The following enclosed code is sample code
The code is provided "AS IS", without warranty of any kind.
'''

import time
import boto3
import json

# athena constant
Database = 'athenacurcfn_athena'

# S3 constant
S3_OUTPUT = 's3://your-s3.bucket'
S3_BUCKET = 'your-s3.bucket'

# number of retries
RETRY_COUNT = 10

def lambda_handler(event, context):
    
    # athena constant
    AccountID = event['AccountID']

    #Time
    Month = event['Month']
    Year =  event['Year']
    
    # created query
    query = "SELECT product_product_name, product_usagetype, line_item_line_item_description, line_item_usage_account_id, year, month, sum (line_item_blended_cost) AS TOTAL FROM %s.athena WHERE month = '%s' AND year = '%s' AND line_item_usage_account_id = '%s' GROUP BY  product_product_name, product_usagetype,  line_item_line_item_description, line_item_usage_account_id, year, month" % (Database, Month, Year, AccountID)
    
    # athena client
    client = boto3.client('athena')

    # Execution
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': Database
        },
        ResultConfiguration={
            'OutputLocation': S3_OUTPUT
        }
    )

    # get query execution id
    query_execution_id = response['QueryExecutionId']
    print(query_execution_id)

    # get execution status
    for i in range(1, 1 + RETRY_COUNT):

        # get query execution
        query_status = client.get_query_execution(QueryExecutionId=query_execution_id)
        query_execution_status = query_status['QueryExecution']['Status']['State']

        if query_execution_status == 'SUCCEEDED':
            print("STATUS:" + query_execution_status)
            break

        if query_execution_status == 'FAILED':
            raise Exception("STATUS:" + query_execution_status)

        else:
            print("STATUS:" + query_execution_status)
            time.sleep(i)
    else:
        client.stop_query_execution(QueryExecutionId=query_execution_id)
        raise Exception('TIME OVER')

    # get query results
    result = client.get_query_results(QueryExecutionId=query_execution_id)
    print(result)

    # get data
    def get_var_char_values(result):
        return [obj['VarCharValue'] for obj in result['Data']]
    header, *rows = result['ResultSet']['Rows']
    header = get_var_char_values(header)
    result = [dict(zip(header, get_var_char_values(row))) for row in rows]
    import json; print(json.dumps(result, indent=2))
    return result