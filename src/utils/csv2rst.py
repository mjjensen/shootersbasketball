#!/usr/bin/env python

'''Convert CSV to reStructuredText tables

A command-line and PythonTk GUI program to do a simple conversion from
CSV files to reStructuredText tables

A. Caird (acaird@gmail.com)
2016

*** from: https://acaird.github.io/2016/02/07/simple-python-gui
'''

from Tkconstants import END, SUNKEN, X
from Tkinter import Tk, Frame, StringVar, Label, Entry, Button, mainloop
import argparse
import csv
import sys
from tabulate import tabulate
import tkFileDialog


def get_output_filename(input_file_name):
    ''' replace the suffix of the file with .rst '''
    return input_file_name.rpartition('.')[0] + '.rst'


def gui():
    '''make the GUI version of this command that is run if no options are
    provided on the command line'''

    def button_go_callback():
        ''' what to do when the "Go" button is pressed '''
        input_file = entry.get()
        if input_file.rsplit('.')[-1] != 'csv':
            statusText.set('Filename must end in ".csv"')
            message.configure(fg='red')
            return
        else:
            table_contents = read_csv(input_file)
            if table_contents is None:
                statusText.set('Error reading file "{}"'.format(input_file))
                message.configure(fg='red')
                return
            output_file = get_output_filename(input_file)
            if write_table(output_file, table_contents):
                statusText.set('Output is in {}'.format(output_file))
                message.configure(fg='black')
            else:
                statusText.set('Writing file '
                               '"{}" did not succeed'.format(output_file))
                message.configure(fg='red')

    def button_browse_callback():
        ''' What to do when the Browse button is pressed '''
        filename = tkFileDialog.askopenfilename()
        entry.delete(0, END)
        entry.insert(0, filename)

    root = Tk()
    frame = Frame(root)
    frame.pack()

    statusText = StringVar(root)
    statusText.set('Press Browse button or enter CSV filename, '
                   'then press the Go button')

    label = Label(root, text='CSV file: ')
    label.pack()
    entry = Entry(root, width=50)
    entry.pack()
    separator = Frame(root, height=2, bd=1, relief=SUNKEN)
    separator.pack(fill=X, padx=5, pady=5)

    button_go = Button(root,
                       text='Go',
                       command=button_go_callback)
    button_browse = Button(root,
                           text='Browse',
                           command=button_browse_callback)
    button_exit = Button(root,
                         text='Exit',
                         command=sys.exit)
    button_go.pack()
    button_browse.pack()
    button_exit.pack()

    separator = Frame(root, height=2, bd=1, relief=SUNKEN)
    separator.pack(fill=X, padx=5, pady=5)

    message = Label(root, textvariable=statusText)
    message.pack()

    mainloop()


def write_table(outputfile, table_contents):
    ''' Write out the .rst file with the table in it
    '''
    with open(outputfile, 'wb') as output_file:
        try:
            output_file.write(tabulate(table_contents,
                                       tablefmt='grid',
                                       headers='firstrow'))
        except BaseException:
            return False
    return True


def command_line(args):
    ''' Run the command-line version
    '''
    if args.output is None:
        args.output = get_output_filename(args.input)

    table_contents = read_csv(args.input)

    if write_table(args.output, table_contents):
        print 'rst table is in file "{}"'.format(args.output)
    else:
        print 'Writing file "{}" did not succeed.'.format(args.output)


def read_csv(filename):
    ''' Read the CSV file

    This fails pretty silently on any exception at all
    '''
    try:
        with open(filename, 'rb') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            reader = csv.reader(csvfile, dialect)
            r = []
            for row in reader:
                r.append(row)
    except BaseException:
        return None

    return r


def get_parser():
    ''' The argument parser of the command-line version '''
    parser = argparse.ArgumentParser(description=('convert csv to rst table'))

    parser.add_argument('--input', '-F',
                        help='name of the intput file')

    parser.add_argument('--output', '-O',
                        help=('name of the output file; ' +
                              'defaults to <inputfilename>.rst'))
    return parser


if __name__ == '__main__':
    ''' Run as a stand-alone script '''

    parser = get_parser()       # Start the command-line argument parsing
    args = parser.parse_args()  # Read the command-line arguments

    if args.input:              # If there is an argument,
        command_line(args)      # run the command-line version
    else:
        gui()                   # otherwise run the GUI version
