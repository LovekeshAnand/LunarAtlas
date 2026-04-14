import math
BASE_BUCKETS= 1000
MINIMUM_BUCKET_SIZE=0.01
DEFAULT_ZOOM_LEVEL=0

def calculate_bucket_size(delta_wavelength,z):
    if z>=0:
        bucket_size=round(float((delta_wavelength)/(BASE_BUCKETS*2**z)),2)
        print("\nBucket size: ", bucket_size)
        return bucket_size

def compute_final_bucket_size(delta_wavelength,z):
    bucket_size=calculate_bucket_size(delta_wavelength, z)
    b_size_final=float(max(MINIMUM_BUCKET_SIZE,bucket_size))
    print("\nFinal bucket size is: ", b_size_final)
    return b_size_final

def compute_total_buckets(delta_wavelength,z):
    b_size_final=compute_final_bucket_size(delta_wavelength,z)
    N=int(math.ceil(delta_wavelength/b_size_final))
    print("\nTotal Number of buckets: ",N)
    return N

def compute_z_max(delta_wavelength,z):
    z_max=int(math.log2(delta_wavelength/(BASE_BUCKETS*MINIMUM_BUCKET_SIZE)))
    print("\nMaximum zoom level: ",z_max)
    if z>z_max:
        print("Zoom won't be supported beyong maximum zoom level, try between minimum range and maximum zoom level.")
    return z_max


def main():
    print("Enter Values required to hard code to understand mathematical formulae\n")
    wavelength_min=float(input("Enter min wave(minimum is 200):"))
    wavelength_max=float(input("Enter max wave(maximum is 900):"))
    z=int(input("Enter the zoom level[3-5 only]: "))
    if wavelength_min<=wavelength_max:
        delta_wavelength=float(wavelength_max-wavelength_min)
        print("\nChange in wavelength:", delta_wavelength)

    compute_total_buckets(delta_wavelength,z)
    
    compute_z_max(delta_wavelength,z)

    print("\nAll 4 functions ran successfully.")

if __name__=="__main__":
    main()








    

