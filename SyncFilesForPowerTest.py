import hashlib
import shutil
import os
import io
import sys
import time
import datetime


class Singleton(object):
    _instance = None

    def __new__(cls, *args, **kw):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kw)  
        return cls._instance  


class SyncFiles(Singleton):

    def __init__(self):
        name, _ = os.path.splitext(os.path.basename(__file__))
        filename = '%s_%s.log' % (name, time.strftime("%Y%m%d%H%M", time.localtime()))
        path = os.getcwd()
        for dir in [r'TestLog', r'SyncRelayFiles']: 
            path = os.path.join(path, dir)
            if not os.path.exists(path):
                os.mkdir(path)
        self.logfile = os.path.join(path, filename)

    def log(self, msg):
        with open(self.logfile, r"a+") as fp:
            print "%s - SyncFiles - Debug - %s" % (datetime.datetime.now(), msg)
            fp.write("%s %s\n" % (datetime.datetime.now(), msg))

    @staticmethod
    def get_md5_of_file(filename):
        md5_value = hashlib.md5()
        file = io.FileIO(filename, 'r')
        bytes = file.read(1024)
        while bytes != b'':
            md5_value.update(bytes)
            bytes = file.read(1024)
        file.close()
        return md5_value

    def sync_one_folder(self, src_dir, dest_dir):
        result = True
        fileitems = os.listdir(src_dir)
        if not fileitems:
            self.log("Cannot find file on %s" % src_dir)
            return False

        if not os.path.exists(dest_dir):
            try:
                os.makedirs(dest_dir)
            except Exception,why:
                self.log("Exception :%s" % why)

        for fileitem in fileitems:
            src_path = os.path.join(src_dir, fileitem)
            dest_path = os.path.join(dest_dir, fileitem)
            if os.path.exists(dest_path):
                if SyncFiles.get_md5_of_file(src_path).hexdigest() ==\
                        SyncFiles.get_md5_of_file(dest_path).hexdigest():
                    continue
            for _ in range(5):
                try:
                    shutil.copy(src_path, dest_path)
                    self.log("[SRC]:%s [DEST]:%s" % (src_path, dest_path))
                    result = True
                    break
                except Exception, why:
                    self.log("Exception: Copied Fail\n%s" % why)
                    result = False
                    time.sleep(5)
        return result

    def sync_singel_file(self, src_file, dest_file):
        result = True
        if os.path.exists(dest_file):
            if self.get_md5_of_file(src_file).hexdigest() == self.get_md5_of_file(dest_file).hexdigest():
                return result
        for _ in range(5):
            try:
                shutil.copy(src_file, dest_file)
                self.log("[SRC]:%s [DEST]:%s" % (src_file, dest_file))
                break
            except Exception, why:
                result = False
                self.log("Exception:%s" % why)
                time.sleep(5)
        return result


if __name__ == '__main__':
    sn = sys.argv[1] if len(sys.argv) == 2 else exit()
    case_path = r'\\shextnas1\spdlogs\BM_SET\POWER_TEST_CASE'
    assist_files = r'\\shextnas1\spdlogs\BM_SET\TestProject\PowerAssistant'
    uicsv_path = r'\\shextnas1\spdlogs\BM_SET\testfiles\UI.csv'
    sync = SyncFiles()
    dest_path = os.path.abspath(os.path.join(os.getcwd(), ".."))
    uicsv_dest_path = os.getcwd().strip('\testcases\ext')
    uicsv_dest_path = os.path.join(os.path.join(uicsv_dest_path,r'plans'), r'UI.csv')
    sync.sync_singel_file(uicsv_path, uicsv_dest_path)
    sync.sync_one_folder(case_path, dest_path)
    sync.sync_one_folder(case_path, os.path.join(dest_path, r'itest'))
    sync.sync_one_folder(assist_files, os.path.join(dest_path, r'itest'))
    sync.log('Total test is pass')
