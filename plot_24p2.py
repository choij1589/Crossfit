import ROOT
import argparse

# Parse the arguments
parser = argparse.ArgumentParser(description="Plot the scores for 24.1")
parser.add_argument("--file", type=str, help="The csv file to read the scores from")
args = parser.parse_args()

# Open the csv file
csv = open(f"{args.file}", "r")
DATE, TIME = args.file.split(".")[1], args.file.split(".")[2]

reps = []
reps_s = []
reps_f = []

for line in csv:
    if "--" in line:
        continue
    elif "- s" in line:
        # scaled
        reps_s.append(int(line.split(" ")[0][1:]))
    elif "- f" in line:
        # foundation
        reps_f.append(int(line.split(" ")[0][1:]))
    else:
        reps.append(int(line.split(" ")[0][1:]))

h_reps = ROOT.TH1F("h_reps", "Open 24.2 score - Rx'd", 240, 0, 90*12)
h_reps_s = ROOT.TH1F("h_reps_s", "Open 24.2 score - Scaled", 240, 0, 90*12)
h_reps_f = ROOT.TH1F("h_reps_f", "Open 24.2 score - Foundation", 240, 0, 90*12)

h_reps.GetXaxis().SetTitle("Reps")
h_reps.GetYaxis().SetTitle("Count")

h_reps_s.GetXaxis().SetTitle("Reps")
h_reps_s.GetYaxis().SetTitle("Count")

h_reps_f.GetXaxis().SetTitle("Reps")
h_reps_f.GetYaxis().SetTitle("Count")

for rep in reps:
    h_reps.Fill(rep)
for rep in reps_s:
    h_reps_s.Fill(rep)
for rep in reps_f:
    h_reps_f.Fill(rep)

h_reps.SetLineColor(ROOT.kBlack)
h_reps.SetLineWidth(2)

h_reps_s.SetLineColor(ROOT.kRed)
h_reps_s.SetLineWidth(2)

h_reps_f.SetLineColor(ROOT.kBlue)
h_reps_f.SetLineWidth(2)

ROOT.gStyle.SetOptStat(0)
c = ROOT.TCanvas("c", "c", 800, 600)
c.cd()

c.Clear()
h_reps.Draw()
c.SaveAs(f"plots/24p2-reps.{DATE}.{TIME}.png")

c.Clear()
h_reps_s.Draw()
c.SaveAs(f"plots/24p2-reps_s.{DATE}.{TIME}.png")

c.Clear()
h_reps_f.Draw()
c.SaveAs(f"plots/24p2-reps_f.{DATE}.{TIME}.png")

