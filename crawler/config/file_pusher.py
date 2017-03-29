from __future__ import print_function
import sys


def main():
    '''
    A manual configuration file pusher for the crawlers. This will update
    Zookeeper with the contents of the file specified in the args.
    '''
    import argparse
    from kazoo.client import KazooClient

    parser = argparse.ArgumentParser(
            description="Crawler config file pusher to Zookeeper")
    parser.add_argument('-f', '--file', action='store', required=True,
                        help="The yaml file to use")
    parser.add_argument('-i', '--id', action='store', default="all",
                        help="The crawler id to use in zookeeper")
    parser.add_argument('-p', '--path', action='store',
                        default="/scrapy-cluster/crawler/",
                        help="The zookeeper path to use")
    parser.add_argument('-w', '--wipe', action='store_const', const=True,
                        help="Remove the current config")
    parser.add_argument('-z', '--zoo-keeper', action='store', required=True,
                        help="The Zookeeper connection <host>:<port>")
    args = vars(parser.parse_args())

    filename = args['file']
    id = args['id']
    wipe = args['wipe']
    zoo = args['zoo_keeper']
    path = args['path']

    zk = KazooClient(hosts=zoo)
    zk.start()

    # ensure path exists
    zk.ensure_path(path)

    bytes = open(filename, 'rb').read()

    if zk.exists(path):
        # push the conf file
        if not zk.exists(path + id) and not wipe:
            print("creaing conf node")
            zk.create(path + id, bytes)
        elif not wipe:
            print("updating conf file")
            zk.set(path + id, bytes)

        if wipe:
            zk.set(path + id, None)

    zk.stop()

if __name__ == "__main__":
    sys.exit(main())
