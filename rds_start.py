"""
SOMETHING
"""
import os
import boto3


def start_rds_all():
    """
    SOMETHING
    """
    region = os.environ['REGION']
    key = os.environ['KEY']
    value = os.environ['VALUE']
    client = boto3.client('rds', region_name=region)
    response = client.describe_db_instances()

    v_read_replica = []
    for i in response['DBInstances']:
        read_replica = i['ReadReplicaDBInstanceIdentifiers']
        v_read_replica.extend(read_replica)

    for i in response['DBInstances']:
        # The if condition below filters aurora clusters
        # from single instance databases as boto3 commands
        # defer to start the aurora clusters.
        if i['Engine'] not in ['aurora-mysql', 'aurora-postgresql']:
            # The if condition below filters Read replicas.
            if i['DBInstanceIdentifier'] not in v_read_replica and len(i['ReadReplicaDBInstanceIdentifiers']) == 0:
                arn = i['DBInstanceArn']
                resp2 = client.list_tags_for_resource(ResourceName=arn)
                # check if the RDS instance is part of the Auto-Shutdown group.
                if 0 == len(resp2['TagList']):
                    print(f'DB Instance {i["DBInstanceIdentifier"]} is not part of autoshutdown')
                else:
                    for tag in resp2['TagList']:
                        if tag['Key'] == key and tag['Value'] == value:
                            if i['DBInstanceStatus'] == 'available':
                                print(f'{i["DBInstanceIdentifier"]} DB instance is already available')
                            elif i['DBInstanceStatus'] == 'stopped':
                                client.start_db_instance(DBInstanceIdentifier=i['DBInstanceIdentifier'])
                                print(f'Started DB Instance {i["DBInstanceIdentifier"]}')
                            elif i['DBInstanceStatus'] == 'starting':
                                print(f'DB Instance {0} is already in starting state')
                            elif i['DBInstanceStatus'] == 'stopping':
                                print(f'DB Instance {i["DBInstanceIdentifier"]} '
                                      f'is in stopping state. Please wait before starting')
                        elif tag['Key'] != key and tag['Value'] != value:
                            print(f'DB instance {i["DBInstanceIdentifier"]} is not part of autoshutdown')
                        elif len(tag['Key']) == 0 or len(tag['Value']) == 0:
                            print(f'DB Instance {i["DBInstanceIdentifier"]} is not part of autoshutdown')
            elif i['DBInstanceIdentifier'] in v_read_replica:
                print(f'DB Instance {i["DBInstanceIdentifier"]} is a Read Replica.')
            else:
                print(f'DB Instance {i["DBInstanceIdentifier"]} has a read replica. '
                      'Cannot shutdown & start a database with Read Replica')

    response = client.describe_db_clusters()
    for i in response['DBClusters']:
        cluarn = i['DBClusterArn']
        resp2 = client.list_tags_for_resource(ResourceName=cluarn)
        if 0 == len(resp2['TagList']):
            print(f'DB Cluster {i["DBClusterIdentifier"]} is not part of autoshutdown')
        else:
            for tag in resp2['TagList']:
                if tag['Key'] == key and tag['Value'] == value:
                    if i['Status'] == 'available':
                        print(f'{i["DBClusterIdentifier"]} DB Cluster is already available')
                    elif i['Status'] == 'stopped':
                        client.start_db_cluster(DBClusterIdentifier=i['DBClusterIdentifier'])
                        print(f'Started Cluster {i["DBClusterIdentifier"]}')
                    elif i['Status'] == 'starting':
                        print(f'cluster {i["DBClusterIdentifier"]} is already in starting state.')
                    elif i['Status'] == 'stopping':
                        print(f'cluster {i["DBClusterIdentifier"]} is in stopping state. Please wait before starting')
                elif tag['Key'] != key and tag['Value'] != value:
                    print(f'DB Cluster {i["DBClusterIdentifier"]} is not part of autoshutdown')
                else:
                    print(f'DB Instance {i["DBClusterIdentifier"]} is not part of autoShutdown')


def lambda_handler(event, context):
    """
    SOMETHING
    """
    start_rds_all()
    print(f'{event}, {context}')
