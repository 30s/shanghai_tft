from distutils.core import setup  
import py2exe  
  
setup(windows=[
        {"script":
             "BinGentor.pyw", 
         "icon_resources": [(1, "bmp.ico")]
         }],
      data_files=[(".", [r".\162.bin", 
                         r".\ASC_GB_TS_0_3_4M_LIB.bin", 
                         r".\ASC_GB_TS_0_4_8M_LIB.bin"
                         ])]
      )
