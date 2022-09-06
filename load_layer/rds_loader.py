"""
RDS Logic
"""
import psycopg2


class RDSLoader:
    """
    Something will be written here later...
    """
    db_port = 5432

    def get_rds_connection(self, host: str, database: str, user: str, password: str):
        """
        This method creates and returns database connection
        """
        connection = psycopg2.connect(host=host,
                                      database=database,
                                      user=user,
                                      password=password,
                                      port=self.db_port)

        return connection

    def load_to_rds(self, connection, table: str, cars: list):
        """
        A method for working with a database.
        The presence of the table
        in the database is checked
        and, if necessary, a creation
        query is executed.
        A query to write data to the database
         in the specified table is also executed.
        """
        crate_table_query = f'CREATE TABLE IF NOT EXISTS {table} ' \
                            f'(date varchar(10), day_of_week varchar(25), ' \
                            f'week_number integer, link varchar(255), ' \
                            f'brand varchar(255), model varchar(255), ' \
                            f'year_of_manufacture integer, engine_type varchar(50), ' \
                            f'engine_volume float, gearbox_type varchar(50), ' \
                            f'mileage integer, price_usd integer, ' \
                            f'location varchar(255), PRIMARY KEY(link))'

        try:
            # Get cursor object from the database connection
            cur = connection.cursor()
            # Creates a table if it does not exist in the database with 'link' as Primary Key
            cur.execute(crate_table_query)
            # INSERT all daily data into table and ignore 'link' duplicates
            for car in cars:
                cur.execute(
                    f'INSERT INTO {table} '
                    f'(date, day_of_week, week_number, '
                    f'link, brand, model, year_of_manufacture, '
                    f'engine_type, engine_volume, gearbox_type, '
                    f'mileage, price_usd, location) '
                    f'VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '
                    f'ON CONFLICT (link) DO NOTHING',
                    (car['date'], car['day_of_week'],
                     car['week_number'], car['link'],
                     car['brand'], car['model'],
                     car['year_of_manufacture'],
                     car['engine_type'], car['engine_volume'],
                     car['gearbox_type'], car['mileage'],
                     car['price_usd'], car['location']))
            # Close cursor object
            cur.close()
            # Save all the modifications made since the last commit
            connection.commit()

        except psycopg2.OperationalError as error:
            print(f'ERROR --------->>>>    Failed to connect to Database! -->>  {error}')
