import ROOT
import argparse

# Parse the arguments
parser = argparse.ArgumentParser(description="Plot the scores for 24.1")
parser.add_argument("--file", type=str, help="The csv file to read the scores from")
args = parser.parse_args()

# Open the csv file
csv = open(f"{args.file}", "r")
DATE, TIME = args.file.split(".")[1], args.file.split(".")[2]
print(DATE, TIME)
times = []
reps = []
for line in csv:
    # Skip the scaled and foundation
    if "- s" in line or "- f" in line:
        continue
    if "--" in line:
        continue
    
    # The format of the line is (MIN:SEC) or (REP reps)
    if "reps" in line:
        reps.append(int(line.split(" ")[0][1:]))
    else:
        minute = int(line.split(":")[0][1:])
        second = int(line.split(":")[1][:-2])
        times.append(minute * 60 + second)

h_times = ROOT.TH1F("h_times", "Open 24.1 score - Rx'd (finished)", 90, 0, 900)
h_reps = ROOT.TH1F("h_reps", "Open 24.1 score - Rx'd (not finished)", 36, 0, 180)

h_times.GetXaxis().SetTitle("Time (s)")
h_times.GetYaxis().SetTitle("Count")
h_reps.GetXaxis().SetTitle("Reps")
h_reps.GetYaxis().SetTitle("Count")
for time in times:
    h_times.Fill(time)
for rep in reps:
    h_reps.Fill(rep)

h_times.SetLineColor(ROOT.kBlack)
h_times.SetLineWidth(2)

h_reps.SetLineColor(ROOT.kBlack)
h_reps.SetLineWidth(2)

ROOT.gStyle.SetOptStat(0)
c = ROOT.TCanvas("c", "c", 800, 600)
c.cd()
h_times.Draw()
c.SaveAs(f"plots/24p1-times.{DATE}.{TIME}.png")

c.Clear()
h_reps.Draw()
c.SaveAs(f"plots/24p1-reps.{DATE}.{TIME}.png")

