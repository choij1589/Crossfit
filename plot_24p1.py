import ROOT
import argparse

# Parse the arguments
parser = argparse.ArgumentParser(description="Plot the scores for 24.1")
parser.add_argument("--file", type=str, help="The csv file to read the scores from")
args = parser.parse_args()

# Open the csv file
csv = open(f"{args.file}", "r")
DATE, TIME = args.file.split(".")[1], args.file.split(".")[2]

times = []
reps = []

times_s = []
reps_s = []

times_f = []
reps_f = []

for line in csv:
    if "--" in line:
        continue
    elif "- s" in line:
        # scaled
        if "reps" in line:
            reps_s.append(int(line.split(" ")[0][1:]))
        else:
            minute = int(line.split(":")[0][1:])
            second = int(line.split(":")[1][:2])
            times_s.append(minute * 60 + second)
    elif "- f" in line:
        # foundation
        if "reps" in line:
            reps_f.append(int(line.split(" ")[0][1:]))
        else:
            minute = int(line.split(":")[0][1:])
            second = int(line.split(":")[1][:2])
            times_f.append(minute * 60 + second)
    else:
        # The format of the line is (MIN:SEC) or (REP reps)
        if "reps" in line:
            reps.append(int(line.split(" ")[0][1:]))
        else:
            minute = int(line.split(":")[0][1:])
            second = int(line.split(":")[1][:2])
            times.append(minute * 60 + second)


h_times = ROOT.TH1F("h_times", "Open 24.1 score - Rx'd (finished)", 90, 0, 900)
h_reps = ROOT.TH1F("h_reps", "Open 24.1 score - Rx'd (not finished)", 36, 0, 180)
h_times_s = ROOT.TH1F("h_times_s", "Open 24.1 score - Scaled (finished)", 90, 0, 900)
h_reps_s = ROOT.TH1F("h_reps_s", "Open 24.1 score - Scaled (not finished)", 36, 0, 180)
h_times_f = ROOT.TH1F("h_times_f", "Open 24.1 score - Foundation (finished)", 90, 0, 900)
h_reps_f = ROOT.TH1F("h_reps_f", "Open 24.1 score - Foundation (not finished)", 36, 0, 180)

h_times.GetXaxis().SetTitle("Time / 10s")
h_times.GetYaxis().SetTitle("Count")
h_reps.GetXaxis().SetTitle("Reps / 5")
h_reps.GetYaxis().SetTitle("Count")

h_times_s.GetXaxis().SetTitle("Time / 10s")
h_times_s.GetYaxis().SetTitle("Count")
h_reps_s.GetXaxis().SetTitle("Reps / 5")
h_reps_s.GetYaxis().SetTitle("Count")

h_times_f.GetXaxis().SetTitle("Time / 10s")
h_times_f.GetYaxis().SetTitle("Count")
h_reps_f.GetXaxis().SetTitle("Reps / 5")
h_reps_f.GetYaxis().SetTitle("Count")

for time in times:
    h_times.Fill(time)
for rep in reps:
    h_reps.Fill(rep)
for time in times_s:
    h_times_s.Fill(time)
for rep in reps_s:
    h_reps_s.Fill(rep)
for time in times_f:
    h_times_f.Fill(time)
for rep in reps_f:
    h_reps_f.Fill(rep)

h_times.SetLineColor(ROOT.kBlack)
h_times.SetLineWidth(2)

h_reps.SetLineColor(ROOT.kBlack)
h_reps.SetLineWidth(2)

h_times_s.SetLineColor(ROOT.kRed)
h_times_s.SetLineWidth(2)

h_reps_s.SetLineColor(ROOT.kRed)
h_reps_s.SetLineWidth(2)

h_times_f.SetLineColor(ROOT.kBlue)
h_times_f.SetLineWidth(2)

h_reps_f.SetLineColor(ROOT.kBlue)
h_reps_f.SetLineWidth(2)

ROOT.gStyle.SetOptStat(0)
c = ROOT.TCanvas("c", "c", 800, 600)
c.cd()
h_times.Draw()
c.SaveAs(f"plots/24p1-times.{DATE}.{TIME}.png")

c.Clear()
h_reps.Draw()
c.SaveAs(f"plots/24p1-reps.{DATE}.{TIME}.png")

c.Clear()
h_times_s.Draw()
c.SaveAs(f"plots/24p1-times_s.{DATE}.{TIME}.png")

c.Clear()
h_reps_s.Draw()
c.SaveAs(f"plots/24p1-reps_s.{DATE}.{TIME}.png")

c.Clear()
h_times_f.Draw()
c.SaveAs(f"plots/24p1-times_f.{DATE}.{TIME}.png")

c.Clear()
h_reps_f.Draw()
c.SaveAs(f"plots/24p1-reps_f.{DATE}.{TIME}.png")

