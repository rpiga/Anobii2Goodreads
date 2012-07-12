# Customise these variables to define input and output

anobii_file = "anobii.csv"
goodreads_file = "import_to_goodreads.csv" 

####### do not change anything below this line

from datetime import date, datetime
import csv, codecs, cStringIO, re
import Tkinter as tk
import tkFileDialog as tkd

root = tk.Tk()
root.withdraw()
file_opt = options = {}
options['title'] = 'Open Anobii CSV file.'
options['filetypes'] = [ ('CSV files', '.csv'), ('text files', '.txt'), ('all files', '.*') ]
options['initialdir'] = '%HOMEPATH%/My Documents'
options['initialfile'] = anobii_file

anobii_file = tkd.askopenfilename(**file_opt)

class UTF8Recoder:
	"""
	Iterator that reads an encoded stream and reencodes the input to UTF-8
	"""
	def __init__(self, f, encoding):
		self.reader = codecs.getreader(encoding)(f)

	def __iter__(self):
		return self

	def next(self):
		return self.reader.next().encode("utf-8")

class UnicodeReader:
	"""
	A CSV reader which will iterate over lines in the CSV file "f",
	which is encoded in the given encoding.
	"""

	def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
		f = UTF8Recoder(f, encoding)
		self.reader = csv.reader(f, dialect=dialect, **kwds)

	def next(self):
		row = self.reader.next()
		return [unicode(s, "utf-8") for s in row]

	def __iter__(self):
		return self

class UnicodeWriter:
	"""
	A CSV writer which will write rows to CSV file "f",
	which is encoded in the given encoding.
	"""

	def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
		# Redirect output to a queue
		self.queue = cStringIO.StringIO()
		self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
		self.stream = f
		self.encoder = codecs.getincrementalencoder(encoding)()

	def writerow(self, row):
		items = []
		for s in row:
			if type(s) == type(u"s"):
				items.append(s.encode("utf8"))
			else:
				items.append(s)

		self.writer.writerow(items)
		# Fetch UTF-8 output from the queue ...
		data = self.queue.getvalue()
		data = data.decode("utf-8")
		# ... and reencode it into the target encoding
		data = self.encoder.encode(data)
		# write to the target stream
		self.stream.write(data)
		# empty queue
		self.queue.truncate(0)

	def writerows(self, rows):
		for row in rows:
			self.writerow(row)


reader = UnicodeReader(open(anobii_file, "rb"))
reader.next() # first line is column titles
target = []

target.append(["Title", "Author", "Additional Authors", "ISBN", "ISBN13", "My Rating", "Average Rating", "Publisher", "Binding", "Year Published", "Original Publication Year", "Date Read", "Date Added", "Bookshelves", "My Review", "Spoiler", "Private Notes", "Recommended For", "Recommended By", "Exclusive Shelf"])

for l in reader:
	isbn = l[0].replace('[', '').replace(']', '')

	title = l[1]
	subtitle = l[2] # Unused
	author = l[3]
	format = l[4]
	pages = l[5] # Unused
	publisher = l[6]

	pubdate = l[7]
	pubyear = ""
	if pubdate:
	    pubyear = pubdate[1:-1].split('-')[0]

	privnote = l[8] # Unused
	commentTitle = l[9] # Unused
	comment = l[10]

	def convertdate(d):
		result = None
		
		for format in ['%b %d, %Y', '%b %Y', '%Y']:
			try:
				result = datetime.strptime(d, format)
			except:
				pass
		
		if result is None:
			return ""

		return result.strftime("%Y/%m/%d")
		
	# Fragile but it works
	# Manage both Finished on and in, to handle different date formats
	status = l[11]
	readdate = ""
	exclusive_shelf = ""
	bookshelves = []
	
	if re.match("^Finished", status):
		if "on" in status or "in" in status:
			readdate = convertdate(status[12:])
		exclusive_shelf = "read"
		
	elif re.match("^Started", status): # Handle as Finished..
		if "on" in status or "in" in status:
			readdate = convertdate(status[11:])
		exclusive_shelf = "read"
	
	elif re.match("^Not Started", status):
		exclusive_shelf = "to-read"
	
	elif re.match("^Reading", status):
		exclusive_shelf = "currently-reading"
	
	elif re.match("^Reference", status):
		exclusive_shelf = "read"
		bookshelves.append("Reference")
	
	elif re.match("^Abandoned", status):
	    if "on" in status:
	        readdate = convertdate(status[13:])
		exclusive_shelf = "abandoned"
		bookshelves.append("Abandoned")
		
	stars = l[12]
	tags = l[13].replace(" ","-").replace("-/-",",")
	
	if (tags): bookshelves.append(tags)
	if (exclusive_shelf <> ""): bookshelves.append(exclusive_shelf)
	
	bookshelves = ",".join(bookshelves)

	tline = [title, author, "", "", isbn, stars, "", publisher, format, pubyear, "", readdate, "", bookshelves, comment, "", privnote, "", "", exclusive_shelf]
	target.append(tline)

	
options['title'] = 'Save output file as'
options['initialfile'] = goodreads_file

goodreads_file = tkd.asksaveasfilename(**file_opt)
writer = UnicodeWriter(open(goodreads_file, "wb"), dialect='excel', quoting=csv.QUOTE_NONNUMERIC)
writer.writerows(target)

print "Done! saved output to " + goodreads_file
