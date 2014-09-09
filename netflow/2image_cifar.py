import csv
import os
import sys
from time import mktime
from time import strptime
from collections import OrderedDict
import operator
from random import shuffle
import pdb
'''
input_dir = sys.argv[1]
output_dir = sys.argv[2]
output_name = sys.argv[3]
'''

input_dir = 'dataset'
output_dir = 'Data'
output_train_name = 'train_batch'
output_test_name = 'test_batch'

NETFLOW_KEYS = ['network.flow.bytes']

TIME_HEADERS = ['time_in_secs']
NETFLOW_HEADERS = NETFLOW_KEYS

def tstamp_to_secs(timestamp):
    localtime = timestamp[0:19]
    timezone = timestamp[19:]
    if timezone == 'Z':
        timezone = 'UTC'
    if len(timezone) == 3:
        time_in_seconds = mktime(strptime(localtime + timezone, '%Y-%m-%dT%H:%M:%S%Z'))
    else:
        tail_number = timezone[1:]
        localtime = localtime[:-2] + str(int(localtime[-2:-1]) + int(tail_number[0])/5)
        time_in_seconds = mktime(strptime(localtime, '%Y-%m-%d %H:%M:%S'))
    return time_in_seconds


all_file_names = os.listdir(input_dir)

# get a list of all instance names in netflow data
netflow_instances = set([])
for filename in all_file_names:
    filepath = os.path.join(input_dir, filename)
    if not os.path.isfile(filepath):
        continue
    with open(filepath) as f:
        while True:
            line = f.readline().rstrip('\n')
            if not line:
                break
            record = eval(line)
            if record['name'] in NETFLOW_KEYS:
                instance_id = record['resource_metadata']['instance_id']
                netflow_instances.add(instance_id)
print netflow_instances
feature_idx_dict = {}
all_headers = TIME_HEADERS + NETFLOW_HEADERS
for idx in range(len(all_headers)):
    feature_idx_dict[all_headers[idx]] = idx

feature_dict = {}
feature_dim = len(all_headers)

for filename in all_file_names:
    filepath = os.path.join(input_dir, filename)
    if not os.path.isfile(filepath):
        continue
    with open(filepath) as f:
        while True:
            line = f.readline().rstrip('\n')
            if not line:
                break
            record = eval(line)
            if record['name'] in NETFLOW_KEYS:
                src_instance_id = record['resource_metadata']['instance_id']
            else:
                continue
            time_stamp = record['timestamp']
            seconds = tstamp_to_secs(time_stamp)
            netflow_dict = record['resource_metadata']['parameters']
            feature_idx = feature_idx_dict.get(record['name'], None)
            for nf in netflow_dict.keys():
                if not nf == 'OUTSIDE':
                #if nf in netflow_instances:
                    dst_instance_id = nf
                    feature_key = (src_instance_id, dst_instance_id, time_stamp)
                    feature_dict.setdefault(feature_key, [0 for d in range(feature_dim)])
                    feature_dict[feature_key][feature_idx] = netflow_dict[nf]
                    feature_dict[feature_key][feature_idx_dict[TIME_HEADERS[0]]] = seconds
    f.close()

sorted_feature_dict = OrderedDict(sorted(feature_dict.iteritems(), key = operator.itemgetter(1)))
'''
output_filepath = os.path.join(output_dir, output_name)
with open(output_filepath, 'wb') as f:
    writer = csv.writer(f)
    #header = ['src_instance_id', 'dst_instance_id'] + TIME_HEADERS + NETFLOW_HEADERS
    header = ['src_dst_instance_id'] + TIME_HEADERS + NETFLOW_HEADERS
    writer.writerow(header)
    for feature_key in sorted_feature_dict.keys():
        (src_instance_id, dst_instance_id, time_stamp) = feature_key
        feature_vect = sorted_feature_dict[feature_key]
        row = list([src_instance_id[0:8] + ' -> ' + dst_instance_id[0:8]] + feature_vect)
        writer.writerow(row)
f.close()
'''
instances = set([])
for feature_key in sorted_feature_dict.keys():
	(src_instance_id, dst_instance_id, time_stamp) = feature_key
	instances.add(src_instance_id)
	instances.add(dst_instance_id)
instances = list(instances)
num_instances = len(instances)
image_dict = [0] * (num_instances * num_instances) 
label = 0
label_list = []
image_list = []
for feature_key in sorted_feature_dict.keys():
	(src_instance_id, dst_instance_id, time_stamp) = feature_key
	timestamp = sorted_feature_dict[feature_key][0]
	if label == 0:
		label = timestamp
	if timestamp < label + 10:
		i = instances.index(src_instance_id)
		j = instances.index(dst_instance_id)
		if image_dict[i * num_instances + j] == 0:
			image_dict[i * num_instances + j] = sorted_feature_dict[feature_key][1]
		else:	
			image_dict[i * num_instances + j] = (image_dict[i * num_instances + j] + sorted_feature_dict[feature_key][1]) / 2
	else:
		label_list.append(label)
		image_list.append(image_dict)
		image_dict = [0] * (num_instances * num_instances)
		label = timestamp
import struct
from PIL import Image
s = [max(i) for i in image_list]
m = max(s)
print m
image_label = zip(image_list, label_list)
num_item = len(image_label)
print num_item
num_train = int(num_item * 0.7)
num_test = num_item - num_train
shuffle(image_label)
train = image_label[:num_train]
train_list, train_label = zip(*train)
test = image_label[num_train:]
test_list, test_label = zip(*test)

output_filepath = os.path.join(output_dir, output_train_name)
f = open(output_filepath, 'wb')
row = num_instances
column = num_instances
print row
#for j in range(num_train):
j = 0
num_channels = 3
while j < num_train-2:
	label = train_label[j]
	if label < 1401238800:
		label = 0
	elif label < 1401249600:
		label = 1
	elif label < 1401255000:
		label = 2
	else:
		label = 3
	f.write(struct.pack("B", label))
	img = Image.new("RGB",(column, row),"white")
	import pdb
	for k in range(j, j + num_channels):
		image = train_list[j]
		for i in range(len(image)):
			pixel = image[i]
			pixel = int(float(pixel) / m * 255)
			#print pixel
			#pixels[int(i / row), i % row][k-j] = pixel
			f.write(struct.pack("B", pixel))
	pixels = zip(train_list[j],train_list[j+1],train_list[j+2])
	img.putdata(pixels)
	image_name = str(label)+"_"+"train" + str(j) + ".png"
	img.save(os.path.join(output_dir,image_name))
	j = j + 3
f.close()

output_filepath = os.path.join(output_dir, output_test_name)
f = open(output_filepath, 'wb')
row = num_instances
column = num_instances
print row
#for j in range(num_train):
j = 0
num_channels = 3
while j < num_test-2:
	label = test_label[j]
	if label < 1401238800:
		label = 0
	elif label < 1401249600:
		label = 1
	elif label < 1401255000:
		label = 2
	else:
		label = 3
	f.write(struct.pack("B", label))
	img = Image.new("RGB",(column, row),"white")
#	pixels = img.load()
	for k in range(j, j + num_channels):
		image = test_list[j]
		for i in range(len(image)):
			pixel = image[i]
			pixel = int(float(pixel) / m * 255)
			#print pixel
#			pixels[int(i / row), i % row][k-j] = pixel
			f.write(struct.pack("B", pixel))
	pixels = zip(test_list[j],test_list[j+1],test_list[j+2])
	img.putdata(pixels)
	image_name =str(label)+"_"+"test"+ str(j) + ".png"
	img.save(os.path.join(output_dir,image_name))
	j = j + 3
f.close()

