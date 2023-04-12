import json
import os
from os import path
from glob import glob
        
class JSONFileField():
    def __init__(self, filename=None, fieldname=None, parent=None, fieldType=object, compact=False, removeTemp=True, fileOnly=False):
        self.subfields = {}
        self.subelements = {}
        self.level = 1
        #self.predefined = predefined
        self.brackets = {list: {'start':'[', 'end':']'}, object: {'start':'{', 'end':'}'}}
        self.fieldType = fieldType
        self.indt = ''
        self.removeTempFiles = removeTemp
        self.isCompact = compact
        self.parent = parent
        self.fileOnly = fileOnly
        
        if self.fileOnly:
            with open(filename, 'r') as in_file:
                self.fileData = json.load(in_file)
       
        else:          
            try:
                self.dataFile = parent.dataFile + '_' + fieldname
                self.rootFile = parent.dataFile
                self.level = parent.level + 1
            except:  
                self.dataFile = filename
                self.rootFile = filename
            
            if self.isCompact:
                self.newLine = ''
                self.indt = ''
                self.parentindt = ''
            else:
                self.newLine = '\n'
                self.indt = '\t'*self.level
                self.parentindt = '\t'*(self.level - 1)
            self.startdelimiter = self.newLine
            
            self.isOpen = True
            #if not self.predefined:
            
            if parent is None and filename is None:
                print('No path or parent specified, no data will be written')
                return None
                
            with open(self.dataFile, 'w') as out_file:
                out_file.write(self.brackets[self.fieldType]['start'])
    
    def write(self, d, recnum=None, timestamp=None, compact=None, prefix=''):
        if not self.isOpen:
            raise Exception("Cannot write to closed field.")
            return False
            
        if compact is None:
            compact = self.isCompact

        with open(self.dataFile, 'a') as out_file: 
            
            if compact:
                out_data = prefix + json.dumps(d, skipkeys=True, indent=None, default=lambda o: self.objdump(o))
            else:
                out_data = (prefix + json.dumps(d, skipkeys=True, indent='\t', default=lambda o: self.objdump(o))).replace('\n', '\n' + self.indt)

            if timestamp is None and recnum is None:
                #if self.predefined and prefix == '':
                #    out_file.write(out_data)    
                #else:
                out_file.write(self.startdelimiter + self.indt + out_data)
            elif timestamp is None:
                if self.fieldType == list:
                    out_file.write(self.startdelimiter + self.indt + '[' + str(recnum) + ', ' + out_data + ']')
                else:
                    out_file.write(self.startdelimiter + self.indt + '"' + str(recnum) + '":' + out_data)
            elif recnum is None:
                out_file.write(self.startdelimiter + self.indt + '[' + str(timestamp) + ', ' + out_data + ']')
            else:
                if self.fieldType == list:
                    out_file.write(self.startdelimiter + self.indt + '[' + str(recnum) + ', ' + str(timestamp) + ', ' + out_data + ']')
                else:
                    out_file.write(self.startdelimiter + self.indt + '"' + str(recnum) + '":[' + str(timestamp) + ', ' + out_data + ']')
                
        if self.startdelimiter == self.newLine or self.startdelimiter == '':
            self.startdelimiter = ',' + self.startdelimiter
            
        return True

    def addField(self, fieldname, fieldType=object):
        if self.isOpen:
            if self.fieldType is list:
                raise Exception("Cannot add field to 'list' type.")
                return None
            newfield = JSONFileField(fieldname=fieldname, parent=self, fieldType=fieldType, compact=self.isCompact, removeTemp=self.removeTempFiles)
            self.subfields[fieldname] = newfield
            return newfield
    
    def addElement(self, elname, data, compact=None):
        if self.write(data, prefix='"' + elname + '":', compact=compact):
            self.subelements[elname] = type(data)
            
    def closeOpenFiles(self, in_dir, removeTemp=True):
        f_list = glob(path.join(in_dir, "*.json_*"))
        base_list = []
        
        for f in f_list:
            base_file = f.split(".json")[0] + ".json"
            if base_file not in base_list:
                base_list.append(base_file)
        print("Found %i unclosed files:\n" % len(base_list))
        
        for f in base_list:
            print("\n--%s" % f)
            self.closeSubFiles(f, removeTemp)
          
          
    def closeSubFiles(self, base_file, removeTemp=True):
        with open(base_file, 'r') as in_file:
            fieldType = self.getFieldType(in_file)    
            
        with open(base_file, 'a') as out_file:     
            sub_list = glob(base_file + "_*")
            sub_fields = []
            all_fields = {}
            field_tree = {}
            
            if len(sub_list) > 0:
                for s in sub_list:
                    all_fields[s] = s.split(base_file)[1].split("_")[1:]
                    #sub_fields[len(all_fields)] = s
                    if len(all_fields[s]) == 1:
                        sub_fields.append(s)
                
                print("\tSubfields of %s: %s" % (base_file, str(sub_fields)))
                    
           
                for f in sub_fields:
                    #print("%s depth: %i" % (s,l))
                    self.closeSubFiles(f)
                        
                    name = all_fields[f][0]
                    
                    with open(f, 'r') as in_file:
                        d = []
                        out_file.write(self.startdelimiter + self.indt + '"' + name + '":')
                        
                        if self.startdelimiter == self.newLine or self.startdelimiter == '':
                            self.startdelimiter = ',' + self.newLine

                        d = in_file.read(1024*1024)
                        while d:
                            out_file.write(d)
                            d = in_file.read(1024*1024)
                    
                    if removeTemp:
                        os.remove(f)
                
            out_file.write(self.newLine + self.brackets[fieldType]['end'])
            print("\Closed %s." % base_file)
           
    def getFieldType(self, in_file):
        d = in_file.read(1)
        in_file.seek(0)
        if d == "{":
            return object
        else:
            return list    
    
        
    def _closeSubFields(self, out_file):
        first = True
        if len(self.subfields) > 0:
            
            if self.level > 1:
                out_file.write(self.parentindt)                
            for name, field in self.subfields.items():
                    
                out_file.write(self.startdelimiter + self.indt + '"' + name + '":')
                
                if self.startdelimiter == self.newLine or self.startdelimiter == '':
                    self.startdelimiter = ',' + self.newLine

                with open(field.dataFile, 'r') as in_file:
                    d = in_file.read(1024*1024)
                    while d:
                        out_file.write(d)
                        d = in_file.read(1024*1024)
                field.close(out_file)
                if self.removeTempFiles:
                    os.remove(field.dataFile)
        #if not self.predefined:
        out_file.write(self.newLine + self.parentindt + self.brackets[self.fieldType]['end']) 
                   
    def close(self, out_file=None):
        if self.isOpen:
            self.isOpen = False
            
            if out_file is None:
                with open(self.rootFile, 'a') as out_file:
                    self._closeSubFields(out_file)                    
            else:
                self._closeSubFields(out_file)
        else:
            print('Field already closed.')
        
        
    def readField(self, field):
        
        if self.fileOnly:
            return field
        
        with open(field.dataFile, 'r') as in_file:
            data = in_file.read()
        if field.isOpen:
            data += (self.newLine + field.brackets[field.fieldType]['end'])
            
        return json.loads(data)
    
    def readAll(self):
        
        if self.fileOnly:
            return self.fileData
              
        out = ''
        first = True
        data = self.readField(self)
        
        if self.level > 0:
            out += self.indt
        for field, name in self.subfields:
            if first:
                out.append('"' + name + '":')
                first = False
            else:
                out.append(',' + self.newLine + '"' + name + '":')
            data += self.readField(field)
        return data

    def objdump(self, o):
        try:
            return o.__dict__
        except:   
            return "Python Object"
    
        
    def __getitem__(self,key):
        
        if self.fileOnly:
            return self.fileData[key]
        
        try:
            return self.subfields[key]
        except:
            return self.subelements[key]
    
    def __str__(self):
        return self.readAll()
        
    def __setitem__(self, key, value):
        return self.addElement(key, data=value)