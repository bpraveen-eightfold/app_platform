import lambda_function


if __name__ == '__main__':
    # TODO: Fill the input variables before running the script
    # For client_id and client_secret, refer to app_platform_app_ef_integration_settings_config
    # For credentials, fill in based on target SFTP server
    client_id = ''
    client_secret = ''
    filename_prefix = 'test'
    timestamp_format = '%Y%m%d_%H%M%S'
    credentials = {
        'host': '',
        'username': '',
        'private_key': {
            'value': ''
        }
    }

    # Get access token
    token_type, access_token = lambda_function.get_access_token(client_id, client_secret)

    # Make request to list-learning-objects API endpoint
    learning_objects = lambda_function.get_learning_objects(token_type, access_token)

    # Pack data into csv
    csv_filename = lambda_function.get_csv_filename(filename_prefix, timestamp_format)
    lambda_function.pack_learning_objects_into_csv(learning_objects, csv_filename)

    # Upload to sftp server
    lambda_function.upload_file_to_sftp(credentials=credentials, filename=csv_filename)
