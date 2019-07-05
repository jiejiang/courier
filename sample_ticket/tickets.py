#!/usr/bin/env python
#*- coding: utf-8 -*
from django.core.files.uploadedfile import InMemoryUploadedFile

__author__ = 'jie'

import optparse, os, glob, sys, shutil, zipfile, re, random
import pandas as pd
from datetime import datetime

def sample_ticket(excel_files, a_indir, n_indir, x_indir, a4_indir, n4_indir, outdir, debug=False, is_jixun=False):
    for folder, folder_name in zip((a_indir, n_indir, x_indir, a4_indir, n4_indir),
                                   (u"爱他美1-3段小票库", u"牛栏1-3段小票库", u"混搭小票库", u"爱他美4段小票库", u"牛栏4段小票库")):
        if not folder or not os.path.exists(folder):
            raise Exception, u"%s 不存在" % folder_name

    dfs = []
    column_names = []
    for excel_file in excel_files:
        df = pd.read_excel(excel_file, converters={
            u'爱他美1-3段单号': lambda x: str(x),
            u'牛栏1-3段单号': lambda x: str(x),
            u'爱他美4段单号': lambda x: str(x),
            u'牛栏4段单号': lambda x: str(x),
            u'其他混和奶粉单号': lambda x: str(x),

            u'爱他美1-3段小票': lambda x: str(x),
            u'牛栏1-3段小票': lambda x: str(x),
            u'爱他美4段小票': lambda x: str(x),
            u'牛栏4段小票': lambda x: str(x),
            u'其他混和奶粉小票': lambda x: str(x),
        })
        a_column = u'爱他美1-3段单号' if u'爱他美1-3段单号' in df.columns else u'爱他美1-3段小票'
        n_column = u'牛栏1-3段单号' if u'牛栏1-3段单号' in df.columns else u'牛栏1-3段小票'
        x_column = u'其他混和奶粉单号' if u'其他混和奶粉单号' in df.columns else u'其他混和奶粉小票'
        a4_column = u'爱他美4段单号' if u'爱他美4段单号' in df.columns else u'爱他美4段小票'
        n4_column = u'牛栏4段单号' if u'牛栏4段单号' in df.columns else u'牛栏4段小票'
        if debug:
            print excel_file, a_column, n_column, x_column, a4_column, n4_column
        dfs.append(df)
        column_names.append((a_column, n_column, x_column, a4_column, n4_column))

    a_files = []
    n_files = []
    x_files = []
    a4_files = []
    n4_files = []

    for indir, files in zip((a_indir, n_indir, x_indir, a4_indir, n4_indir),
                            (a_files, n_files, x_files, a4_files, n4_files)):
        if indir:
            for filename in os.listdir(indir):
                filepath = os.path.join(indir, filename)
                if os.path.isfile(filepath) and filename.lower().endswith(".jpg"):
                    files.append(filepath)

    if debug:
        print len(a_files), len(n_files), len(x_files), len(a4_files), len(n4_files)

    orders_list = []
    a_total = 0
    n_total = 0
    x_total = 0
    a4_total = 0
    n4_total = 0
    for df, (a_column, n_column, x_column, a4_column, n4_column) in zip(dfs, column_names):
        a_orders = df[pd.notnull(df[a_column])][a_column]
        n_orders = df[pd.notnull(df[n_column])][n_column]
        x_orders = df[pd.notnull(df[x_column])][x_column]
        a4_orders = df[pd.notnull(df[a4_column])][a4_column]
        n4_orders = df[pd.notnull(df[n4_column])][n4_column]
        orders_list.append((a_orders, n_orders, x_orders, a4_orders, n4_orders))
        a_total += len(a_orders)
        n_total += len(n_orders)
        x_total += len(x_orders)
        a4_total += len(a4_orders)
        n4_total += len(n4_orders)
    if debug:
        print a_total, n_total, x_total, a4_total, n4_total
    if a_total > len(a_files):
        raise Exception, u"爱他美1-3小票不够"
    if n_total > len(n_files):
        raise Exception, u"牛栏1-3小票不够"
    if x_total > len(x_files):
        raise Exception, u"混搭小票不够"
    if a4_total > len(a4_files):
        raise Exception, u"爱他美4段小票不够"
    if n4_total > len(n4_files):
        raise Exception, u"牛栏4段小票不够"
    random.seed(datetime.now())
    a_samples = random.sample(a_files, a_total)
    random.seed(datetime.now())
    n_samples = random.sample(n_files, n_total)
    random.seed(datetime.now())
    x_samples = random.sample(x_files, x_total)
    random.seed(datetime.now())
    a4_samples = random.sample(a4_files, a4_total)
    random.seed(datetime.now())
    n4_samples = random.sample(n4_files, n4_total)
    samples = [a_samples, n_samples, x_samples, a4_samples, n4_samples]
    indexes = [0, 0, 0, 0, 0]
    for excel_file, (a_orders, n_orders, x_orders, a4_orders, n4_orders) in zip(excel_files, orders_list):
        if debug:
            print len(a_orders), len(n_orders), len(x_orders), len(a4_orders), len(n4_orders), indexes
        filename = excel_file.name if isinstance(excel_file, InMemoryUploadedFile) else os.path.basename(excel_file)
        outfolder = os.path.join(outdir, os.path.splitext(filename)[0])
        if os.path.exists(outfolder):
            raise Exception, "Outdir exists: %s" % outfolder
        os.makedirs(outfolder)

        for i, orders in enumerate((a_orders, n_orders, x_orders, a4_orders, n4_orders)):
            files_sel = samples[i][indexes[i]:indexes[i]+len(orders)]
            count = 0
            for filepath, order_number in zip(files_sel, orders):
                out_suffix = '.x.jpg.jpg' if is_jixun else '.jpg'
                shutil.copy(filepath, os.path.join(outfolder, order_number.strip() + out_suffix))
                count += 1
            if debug:
                print "copied %d" % count
            indexes[i] += len(orders)
        if debug:
            print "saved to: %s" % outfolder

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-a", dest="a_indir")
    parser.add_option("-n", dest="n_indir")
    parser.add_option("-x", dest="x_indir")
    parser.add_option("--a4", dest="a4_indir")
    parser.add_option("--n4", dest="n4_indir")
    parser.add_option("-o", dest="outdir")

    options, excel_files = parser.parse_args()

    if not options.a_indir or not options.n_indir or not options.x_indir or not options.a4_indir or not options.n4_indir \
            or not options.outdir or not excel_files:
        parser.print_help(sys.stderr)
        exit(1)

    sample_ticket(excel_files, options.a_indir, options.n_indir, options.x_indir, options.a4_indir, options.n4_indir,
                  options.outdir)


