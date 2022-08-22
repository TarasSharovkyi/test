


def lambda_handler(event, context):
    # Input parameters
    bucket_name = 'ts-mybucket-03'
    read_prefix = 'yelp/'
    dest_prefix = '/yelp_ready_to_load/'

    from_s3 = get_objects_names_from_bucket(bucket_name, read_prefix)
    data = read_from_s3(from_s3, read_prefix)
    write_to_s3(bucket_name, data, dest_prefix)

    return {
        'statusCode': 200,
        'body': '    ----    >>>>    yelp_academic_dataset_business.json successfully converted to Business.json and Attributes.json'
    }
