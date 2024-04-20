import subprocess
import time

import os
import csv

#root_dir = r"C:\Users\micro\OneDrive\Documents\FrameView\Surface Laptop Studio NEW"
#target_file = f"C:/Users/micro/OneDrive/Documents/FrameView/sls_complete.csv"

root_dir = r"C:\Users\micro\OneDrive\Documents\FrameView\Upscaling + FG"
target_file = f"C:/Users/micro/OneDrive/Documents/FrameView/upscaling_fg_complete.csv"

#root_dir = r"C:\Users\micro\OneDrive\Documents\FrameView\Upscaling + DLSS FG + RayReconstruction"
#target_file = f"C:/Users/micro/OneDrive/Documents/FrameView/upscaling_dlss_fg_rr_complete.csv"

#root_dir = r"C:\Users\micro\OneDrive\Documents\FrameView\Versions"
#target_file = f"C:/Users/micro/OneDrive/Documents/FrameView/upscaling_dlss_versions_complete.csv"
 

def handle_csv(file_path, game, cap, tech, config):

    run_name = f"{game} / {cap} / {tech} / {config}"
    print(f"Handling {file_path}")
    with open(file_path, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        num_frames = 0
        sum_frame_time = 0
        sum_gpu_frame_energy = 0
        sum_cpu_frame_energy = 0

        sum_gpu_temp = 0
        sum_cpu_temp = 0

        sum_gpu_util = 0
        sum_cpu_util = 0

        sum_gpu_clk = 0
        sum_gpu_mem_clk = 0
        sum_cpu_clk = 0

        cpu_package_power_missed_frames = 0

        try:
            for idx, row in enumerate(csvreader):
                if idx == 0:
                    continue
                
                offset = 1 # 0 in old format where MsBetweenSimulationStart on pos 13
                ms_between_presents = float(row[14-offset])
                #ms_between_display_change = row[15-offset]

                #gpu_pc_latency_ms = float(row[20-offset])
                gpu_clk = float(row[21-offset])
                gpu_mem_clk = float(row[22-offset])
                gpu_util = float(row[23-offset])
                gpu_temp = float(row[24-offset])

                perfperwatt_total = float(row[31-offset])
                perfperwatt_gpu_only = float(row[32-offset])
                perfperwatt_usb_c_total = float(row[33-offset])
                power_gpu_only = float(row[34-offset])
                power_gpu_usb_c_total = float(row[35-offset])
                power_nvidia_total = float(row[36-offset])

                cpu_clk = float(row[38-offset])
                cpu_utilization = float(row[39-offset])
                cpu_package_temp = float(row[40-offset])

                # Some frames are missing CPU package power...
                no_cpu_package_power = False
                try:
                    cpu_package_power = float(row[41-offset])
                except ValueError as error:
                    no_cpu_package_power = True

                cpu_tdp = float(row[42-offset])
                cpu_core_util_0 = float(row[43-offset])
                #print(f"CPU stats {cpu_clk} {cpu_utilization} {cpu_package_power} {cpu_tdp} {cpu_core_util_0}")

                frame_time_s = float(ms_between_presents) / 1000
                fps = 1/frame_time_s
                gpu_frame_energy_gpu_only = frame_time_s * power_gpu_only
                gpu_frame_energy_usb_c = frame_time_s * power_gpu_usb_c_total
                gpu_frame_energy_total = frame_time_s * power_nvidia_total

                #PerfPerWatt ((f/s) / (J/s))
                my_perf_per_watt_1 = fps / (gpu_frame_energy_total / frame_time_s)
                #PerfPerWatt(1/t / J/s))
                my_perf_per_watt_2 = (1/frame_time_s) / (gpu_frame_energy_total / frame_time_s)
                #PerfPerWatt (f / s) / (W)
                my_perf_per_watt_3 = fps / power_nvidia_total
                #PerfPerWatt (1/t) / W
                my_perf_per_watt_4 = (1/frame_time_s) / power_nvidia_total
                
                my_perf_per_watt_gpu_only = fps / power_gpu_only
                my_perf_per_watt_usb_c = fps / power_gpu_usb_c_total
                my_perf_per_watt_total = fps / power_nvidia_total

                num_frames += 1
                sum_frame_time += frame_time_s

                sum_gpu_frame_energy += gpu_frame_energy_total

                if no_cpu_package_power: # Do not affect average if we were not able to catch CPU power
                    cpu_package_power_missed_frames += 1
                else:
                    cpu_frame_energy = cpu_package_power * frame_time_s
                    sum_cpu_frame_energy += cpu_frame_energy

                # Not used yet?
                sum_gpu_temp += gpu_temp
                sum_cpu_temp += cpu_package_temp

                sum_gpu_util += gpu_util
                sum_cpu_util += cpu_utilization

                sum_gpu_clk += gpu_clk
                sum_gpu_mem_clk += gpu_mem_clk
                sum_cpu_clk += cpu_clk

                # print(f"Frame time is {frame_time_s}")
                # print(f"FPS is {fps}")
                # print(f"PerfPerWatt is {perfperwatt_gpu_only} {perfperwatt_usb_c_total} {perfperwatt_total}")
                # print(f"My perf per watts are {my_perf_per_watt_gpu_only} {my_perf_per_watt_usb_c} {my_perf_per_watt_total}")
                # print(f"Power is {power_gpu_only} {power_gpu_usb_c_total} {power_nvidia_total}")
                # print(f"Frame energy is {frame_energy_gpu_only} {frame_energy_usb_c} {frame_energy_total}")
        except ValueError as error:
            #print(error)
            import traceback
            print(traceback.format_exc())
            exit(1)
            # import sys
            # exc_type, exc_obj, exc_tb = sys.exc_info()
            # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            # print(exc_type, fname, exc_tb.tb_lineno)
            # exit(1)

        average_gpu_power = sum_gpu_frame_energy / sum_frame_time
        total_perf_per_watt = (num_frames / sum_frame_time) / (sum_gpu_frame_energy / sum_frame_time)
        average_frame_time = sum_frame_time / num_frames
        average_fps = 1/average_frame_time
        average_gpu_frame_energy = sum_gpu_frame_energy / num_frames
        #print(f"{num_frames} {sum_frame_time} {sum_gpu_frame_energy} {average_gpu_power} {total_perf_per_watt} {average_frame_time} {average_fps} {average_gpu_frame_energy}")

        average_cpu_frame_energy = sum_cpu_frame_energy / (num_frames-cpu_package_power_missed_frames)
        average_cpu_power = sum_cpu_frame_energy / sum_frame_time
        #print(f"{sum_cpu_frame_energy} {average_cpu_power} {average_cpu_frame_energy}")

        average_gpu_temp = sum_gpu_temp / num_frames
        average_cpu_temp = sum_cpu_temp / num_frames

        average_gpu_util = sum_gpu_util / num_frames
        average_cpu_util = sum_cpu_util / num_frames

        average_gpu_clk = sum_gpu_clk / num_frames
        average_gpu_mem_clk = sum_gpu_mem_clk / num_frames
        average_cpu_clk = sum_cpu_clk / num_frames

        with open(target_file, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([run_name, num_frames, sum_frame_time, sum_gpu_frame_energy, average_gpu_power, total_perf_per_watt, average_frame_time, average_fps, average_gpu_frame_energy, sum_cpu_frame_energy, average_cpu_power, average_cpu_frame_energy, average_gpu_temp, average_cpu_temp, average_gpu_util, average_cpu_util, average_gpu_clk, average_gpu_mem_clk, average_cpu_clk])

def main():
    
    try:
        os.remove(target_file)
    except FileNotFoundError:
        pass

    with open(target_file, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Name", "Sum frames", "Sum frame time", "Sum GPU Energy", "Average GPU Power", "Total Perf Per Watt", "Average_frame_time", "Average FPS", "Average GPU frame energy", "Sum CPU Energy", "Average CPU Power", "Average CPU Frame energy", "Average GPU Temp", "Average CPU Temp", "Average GPU Util", "Average CPU Util", "Average GPU Clk", "Average GPU Mem Clk", "Average CPU Clk"])

    for game_dir in os.listdir(root_dir):
        game_dir_path = os.path.join(root_dir, game_dir)
        for cap_dir in os.listdir(game_dir_path): # TODO: Remove this when shifting to NEW
            cap_dir_path = os.path.join(game_dir_path, cap_dir) 
            for tech_dir in os.listdir(cap_dir_path):
                tech_dir_path = os.path.join(cap_dir_path, tech_dir)
                for config_dir in os.listdir(tech_dir_path):
                    config_dir_path = os.path.join(tech_dir_path, config_dir)
                    for file in os.listdir(config_dir_path):
                        if file.endswith("_Log.csv"):
                            file_path = os.path.join(config_dir_path, file)
                            handle_csv(file_path, game_dir, cap_dir, tech_dir, config_dir)

    

if __name__ == "__main__":
    main()