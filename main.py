import re
import random
import pickle
import sys
import getopt

import requests
from bs4 import BeautifulSoup
import numpy as np

__author__ = "rafal stempowski"
__date__ = "$2015-10-10 20:10:03$"


def row_column_delete(matrix, number):
    result = np.delete(np.array(matrix), number, axis=1)
    result = np.delete(result, number, axis=0)
    return result.tolist()


def help_message():
    print("wikipediaCrawler.py v.", 2)
    print("Available options:")
    print("-h  --->  Help")
    print("-w  --->  title of polish Wikipedia site to crawl")
    print("-v  --->  (1000) number of wikipedia sites(Vertices) to be crawled")
    print("-l  --->  name of file with serialized graph to Load")
    print("-s  --->  name of the file to Save serialized graph")
    print("-g  --->  name of the file to save Graph")
    print("-c  --->  (90-w/0-l) percent of graph to Clear with heuristics")
    print("-r  --->  (10) chance of deleting Random vertex in graph in  heuristic method")
    print("-d  --->  (0) percent of vertices to be Deleted randomly after heuristics")
    print('-e  --->  if Empty(without edges) vertices will be removed')
    sys.exit()


def parse_entry(argv):
    dictionary = {'r': 10, 'd': 0, 'v': 1000, 'e': False}
    try:
        opts, args = getopt.getopt(argv, "hw:l:s:g:c:r:d:e")
    except:
        help_message()
    for opt, arg in opts:
        if opt == '-h':
            help_message()
        elif opt == '-w':
            if 'load' in dictionary:
                print("Either load from file, or from wikipedia\n\n")
                help_message()
                sys.exit(2)
            dictionary['wiki'] = arg
            if 'c' not in dictionary:
                dictionary['c'] = 90
        elif opt == '-l':
            if 'wiki' in dictionary:
                print("Either load from file, or from wikipedia\n\n")
                help_message()
                sys.exit(2)
            dictionary['load'] = arg
            if 'c' not in dictionary:
                dictionary['c'] = 0
        elif opt == '-s':
            dictionary['save'] = arg
        elif opt == '-g':
            dictionary['graph'] = arg
        elif opt == '-c':
            dictionary['c'] = int(arg)
        elif opt == '-r':
            dictionary['r'] = int(arg)
        elif opt == '-d':
            dictionary['d'] = int(arg)
        elif opt == '-e':
            dictionary['e'] = True
        elif opt == '-v':
            dictionary['v'] = int(arg)
    return dictionary


class Crawler:
    def __init__(self, number, name):
        self.que = []
        self.que.append((name, "/wiki/" + name))
        self.num = number
        self.names = [name]
        self.numOfNewSites = [0]
        self.matrix = [[0 for x in range(number + 40)] for x in range(number + 40)]

    def delete_empty_vertices(self):
        for i in range(len(self.names) - 1, -1, -1):
            bo = 0
            for j in range(0, len(self.names)):
                if self.matrix[i][j] != 0:
                    bo = 1
                    break
            if bo == 1:
                continue
            for j in range(0, len(self.names)):
                if self.matrix[j][i] != 0:
                    bo = 1
                    break
            if bo == 1:
                continue
            self.usunKon(i)

    def clear_randomly(self, percent):
        if percent == 0:
            return
        dl = len(self.names)
        for i in range(1, int(dl * (percent / 100))):
            us = random.randint(0, dl - i)
            self.names.pop(us)
            self.matrix = row_column_delete(self.matrix, us)

    def clear(self, percent_delete, percent_randomly):
        deleted = 0
        if percent_delete == 0:
            return
        for j in range(0, len(self.numOfNewSites) - 1):
            if self.numOfNewSites[j] < 1:
                continue
            od = self.numOfNewSites[j]
            do = self.numOfNewSites[j + 1]
            sum_array = [[0 for x in range(2)] for x in range(do - od)]
            for i in range(od, do):
                sum_array[i - od][0] = sum(self.matrix[i - deleted])
                sum_array[i - od][1] = i
            delete_amount = int((do - od) * (percent_delete / 100))
            sum_array.sort()
            to_delete_array = []
            while delete_amount > 0:
                if random.randint(0, 100) > (100 - percent_randomly):
                    to_delete = random.randint(0, len(sum_array) - 1)
                    to_delete_array.append(sum_array[to_delete][1])
                    delete_amount -= 1
                    sum_array.pop(to_delete)
                else:
                    to_delete = random.randint(0, delete_amount - 1)
                    to_delete_array.append(sum_array[to_delete][1])
                    delete_amount -= 1
                    sum_array.pop(to_delete)
            to_delete_array.sort()
            for i in to_delete_array:
                self.names.pop(i - deleted)
                self.matrix = row_column_delete(self.matrix, i - deleted)
                deleted += 1

    def _delete_ending_help_array(self):
        tmp = 0
        for i in range(1, len(self.numOfNewSites)):
            if self.numOfNewSites[i] != self.numOfNewSites[i - 1]:
                tmp += 1
        self.numOfNewSites = self.numOfNewSites[:tmp + 1]

    def _delete_redundant_matrix(self):
        deleted = 0
        for i in range(0, len(self.matrix)):
            if i >= len(self.names):
                self.matrix = row_column_delete(self.matrix, i - deleted)
                deleted += 1

    def save_graph(self, graph_name):
        with open(graph_name + ".txt", 'w') as output:
            output.write(graph_name + "\n")
            output.write(str(len(self.names)) + "\n")
            for i in self.names:
                output.write(i + "\n")
            for i in range(0, len(self.names)):
                for j in range(0, len(self.names)):
                    if self.matrix[i][j] == 1:
                        output.write(str(i) + "\n")
                        output.write(str(j) + "\n")

    def crawl(self):
        count = 0
        base_url = "https://pl.wikipedia.org"
        finished = False
        while len(self.que) > 0:
            count += 1
            if len(self.names) != self.numOfNewSites[-1]:
                self.numOfNewSites.append(len(self.names))
            element = self.que.pop(0)
            print("Adding page nr " + str(count) + " -- " + element[0])
            url = base_url + element[1]
            current_name = element[0]
            site_text = requests.get(url).text
            site_object = BeautifulSoup(site_text, "html.parser")
            tags = []
            for a in site_object.findAll('a'):
                if len(a.attrs) == 2:
                    if 'href' in a.attrs:
                        if 'title' in a.attrs:
                            if re.match("\/wiki\/[a-zA-Z0-9_%]+", a.attrs['href']):
                                if re.match("\/wiki\/[a-zA-Z0-9_%]+", a.attrs['href']).group(0) == a.attrs['href']:
                                    tags.append(a)
            links = []
            for tag in tags:
                links.append((tag.attrs['title'], tag.attrs['href']))
            links = sorted(set(links))

            for link in links:
                if not link[0] in self.names:
                    if finished:
                        continue
                    self.names.append(link[0])
                    self.que.append(link)
                self.matrix[self.names.index(current_name)][self.names.index(link[0])] = 1

                if len(self.names) > self.num:
                    finished = True
        self._delete_ending_help_array()
        self._delete_redundant_matrix()


def main(argv):
    dictionary = parse_entry(argv)

    if 'save' not in dictionary and 'graph' not in dictionary:
        print("Choose some method of saving.\n\n")
        help_message()

    if 'wiki' in dictionary:
        crawl = Crawler(dictionary['v'], dictionary['wiki'])
        crawl.crawl()
    elif 'load' in dictionary:
        with open(dictionary['load'], 'rb') as input:
            crawl = pickle.load(input)
    else:
        print("Nothing was choosen to process.\n\n")
        help_message()

    crawl.clear(dictionary['c'], dictionary['r'])
    crawl.clear_randomly(dictionary['d'])
    if dictionary['e']:
        crawl.delete_empty_vertices()

    if 'save' in dictionary:
        with open(dictionary['save'], 'wb') as output:
            pickle.dump(crawl, output, pickle.HIGHEST_PROTOCOL)
    if 'graph' in dictionary:
        crawl.save_graph(dictionary['graph'])


if __name__ == "__main__":
    main(sys.argv[1:])
