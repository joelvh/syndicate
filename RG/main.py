#!/usr/bin/env python
# Copyright 2013 The Trustees of Princeton University
# All Rights Reserved

import sys
import syndicate.rg.common as rg_common
import syndicate.rg.closure as rg_closure
import syndicate.rg.server as rg_server
import argparse
import socket
import os

from wsgiref.simple_server import make_server 

log = rg_common.get_logger(__name__)

CONFIG_OPTIONS = {
   "gateway":           ("-g", 1, "The name of this RG"),
   "volume":            ("-v", 1, "The Volume this RG runs in"),
   "config":            ("-c", 1, "Path to the Syndicate configuration file for this RG"),
   "username":          ("-u", 1, "Syndicate username of the owner of this RG"),
   "password":          ("-p", 1, "If authenticating via OpenID, the Syndicate user's OpenID password"),
   "port":              ("-P", 1, "Port number to listen on"),
   "MS":                ("-m", 1, "Syndicate MS URL"),
   "volume_pubkey":     ("-V", 1, "Path to the PEM-encoded Volume public key"),
   "gateway_pkey":      ("-G", 1, "Path to the PEM-encoded RG private key"),
   "tls_pkey":          ("-S", 1, "Path to the PEM-encoded RG TLS private key.  Use if you want TLS for data transfers (might cause breakage if your HTTP caches do not expect TLS)."),
   "tls_cert":          ("-C", 1, "Path to the PEM-encoded RG TLS certificate.  Use if you want TLS for data transfers (might cause breakage if your HTTP caches do not expect TLS)."),
   "foreground":        ("-f", 0, "Run in the foreground"),
   "logdir":            ("-L", 1, "Directory to contain the log files.  If not given, then write to stdout and stderr."),
   "pidfile":           ("-l", 1, "Path to the desired PID file.")
}

#-------------------------
def load_config( config_str, opts ):
   
   config = None 
   
   if config_str:
      config = ConfigParser.SafeConfigParser()
      config_fd = StringIO.StringIO( config_str )
      config_fd.seek( 0 )
      
      try:
         config.readfp( config_fd )
      except Exception, e:
         log.exception( e )
         return None
   
   ret = {}
   ret["_in_argv"] = []
   ret["_in_config"] = []
   
   # convert to dictionary, merging in argv opts
   for arg_opt in CONFIG_OPTIONS.keys():
      if hasattr(opts, arg_opt) and getattr(opts, arg_opt) != None:
         ret[arg_opt] = getattr(opts, arg_opt)
         
         # force singleton...
         if isinstance(ret[arg_opt], list) and len(ret[arg_opt]) == 1 and CONFIG_OPTIONS[arg_opt][1] == 1:
            ret[arg_opt] = ret[arg_opt][0]
            
         ret["_in_argv"].append( arg_opt )
      
      elif config != None and config.has_option("Replica Gateway", arg_opt):
         ret[arg_opt] = config.get("Replica Gateway", arg_opt)
         
         ret["_in_config"].append( arg_opt )
   
   return ret

#-------------------------
def build_parser( progname ):
   parser = argparse.ArgumentParser( prog=progname, description="Syndicate Replica Gateway" )
   
   for (config_option, (short_option, nargs, config_help)) in CONFIG_OPTIONS.items():
      if not isinstance(nargs, int) or nargs >= 1:
         if short_option:
            # short option means 'typical' argument
            parser.add_argument( "--" + config_option, short_option, metavar=config_option, nargs=nargs, help=config_help)
         else:
            # no short option (no option in general) means accumulate
            parser.add_argument( config_option, metavar=config_option, type=str, nargs=nargs, help=config_help)
      else:
         # no argument, but mark its existence
         parser.add_argument( "--" + config_option, short_option, action="store_true", help=config_help)
   
   return parser

#-------------------------
def validate_args( config ):
   
   # check types...
   try:
      gateway_portnum = int(config['port'])
   except:
      log.error("Invalid or missing port: %s" % config.get("port", None))
      return False
   
   paths = []
   for path_type in ['volume_pubkey', 'gateway_pkey', 'tls_pkey', 'tls_cert']:
      if config.get( path_type, None ) != None:
         paths.append( config[path_type] )
   
   # check paths and readability
   invalid = False
   for file_path in paths:
      if not os.path.exists( file_path ):
         log.error("Path '%s' does not exist" % (file_path))
         invalid = True
      
      else:
         try:
            fd = open(file_path, "r")
         except OSError:
            log.error("Cannot read '%s'" % (file_path))
            invalid = True
         finally:
            fd.close()
         
   if invalid:
      return False
      
   return True
      
#-------------------------
def setup_syndicate( config ):
   
   gateway_portnum = int(config['port'])
   gateway_name = config.get('gateway', None)
   rg_username = config.get('username', None)
   rg_password = config.get('password', None)
   ms_url = config.get('MS', None)
   my_key_file = config.get('gateway_pkey', None)
   volume_name = config.get('volume', None)
   volume_pubkey = config.get('volume_pubkey', None)
   tls_pkey = config.get('tls_pkey', None)
   tls_cert = config.get('tls_cert', None)
   config_file = config.get('config_file', None)
   
   # start up libsyndicate
   syndicate = rg_common.syndicate_init( ms_url=ms_url,
                                         gateway_name=gateway_name,
                                         portnum=gateway_portnum,
                                         volume_name=volume_name,
                                         gateway_cred=rg_username,
                                         gateway_pass=rg_password,
                                         my_key_filename=my_key_file,
                                         conf_filename=config_file,
                                         volume_key_filename=volume_pubkey,
                                         tls_pkey_filename=tls_pkey,
                                         tls_cert_filename=tls_cert )
   
   return syndicate 

#-------------------------
def run( config, syndicate )

   # get our hostname
   hostname = socket.gethostname()
   
   # get our key file and port 
   my_key_file = config.get("gateway_pkey", None )
   gateway_portnum = int( config['port'] )
   
   # get our configuration from the MS and start keeping it up to date 
   rg_closure.init( syndicate, my_key_file )

   # start serving
   httpd = make_server( hostname, gateway_portnum, rg_server.wsgi_application )
   
   httpd.serve_forever()
   
   return True
   

#-------------------------
def debug():
   
   rg_common.syndicate_lib_path( "../python" )
   
   gateway_name = "RG-t510-0-690"
   gateway_portnum = 24160
   rg_username = "jcnelson@cs.princeton.edu"
   rg_password = "nya!"
   ms_url = "http://localhost:8080/"
   my_key_file = "../../../replica_manager/test/replica_manager_key.pem"
   volume_name = "testvolume-jcnelson-cs.princeton.edu"
   
   # start up libsyndicate
   syndicate = rg_common.syndicate_init( ms_url=ms_url, gateway_name=gateway_name, portnum=gateway_portnum, volume_name=volume_name, gateway_cred=rg_username, gateway_pass=rg_password, my_key_filename=my_key_file )
   
   # start up config
   rg_closure.init( syndicate, my_key_file )
   
   # start serving!
   httpd = make_server( "t510", gateway_portnum, rg_server.wsgi_application )
   
   httpd.serve_forever()
   
   return True 

#-------------------------
def build_config( argv ):
   
   parser = build_parser( argv[0] )
   opts = parser.parse_args( argv[1:] )
   config = load_config( None, opts )
   
   if config == None:
      log.error("Failed to load configuration")
      parser.print_help()
      sys.exit(1)
   
   rc = validate_args( config )
   if not rc:
      log.error("Invalid arguments")
      parser.print_help()
      sys.exit(1)
      
   return config
      
#-------------------------
def main( config ):
   syndicate = setup_syndicate( config )
   run( config, syndicate )
   #debug()
   

#-------------------------    
if __name__ == "__main__":
   config = build_config( argv )
   main( config )