param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($RepositoryRoot)
$scenarioPath = Join-Path $root "mod\scenarios\1933\british raj.inc"
$leaderPath = Join-Path $root "mod\db\leaders\india.csv"
$encoding = [System.Text.Encoding]::GetEncoding(1252)

$scenario = [System.IO.File]::ReadAllText($scenarioPath, $encoding)
$firstUnitAnchor = $scenario.IndexOf(
    "Ceylon Territorial Command",
    [System.StringComparison]::Ordinal
)
if ($firstUnitAnchor -lt 0) {
    throw "Could not find the first India land-unit marker in $scenarioPath"
}

$start = $scenario.LastIndexOf("landunit", $firstUnitAnchor, [System.StringComparison]::Ordinal)
$start = $scenario.LastIndexOf("`n", $start) + 1
$marker = "   # V4 operational organization: three-unit corps reduce map micro."
$markerAnchor = $scenario.IndexOf($marker, [System.StringComparison]::Ordinal)
if ($markerAnchor -ge 0 -and $markerAnchor -lt $firstUnitAnchor) {
    $start = $markerAnchor
}

$navalAnchor = $scenario.IndexOf("navalunit = {", $firstUnitAnchor, [System.StringComparison]::Ordinal)
if ($navalAnchor -lt 0) {
    throw "Could not find the India naval-unit marker in $scenarioPath"
}
$end = $navalAnchor

$landForces = @'
   # V4 operational organization: three-unit corps reduce map micro.
   # Darkest Hour cannot nest major-generals beneath a corps counter. Players
   # can detach any division and assign a major-general when independent duty
   # is required; institutional exercises represent the wider officer bench.

   landunit = {
      name = "Ceylon Territorial Command"
      location = 1511
      id = { type = 12700 id = 14 }
      Division = {
         id = { type = 12700 id = 15 }
         name = "Ceylon Defence Force"
         type = militia
         model = 3
         strength = 70
      }
   }

   landunit = {
      name = "I Southern Corps"
      location = 1516
      leader = 250021
      id = { type = 12700 id = 9001 }
      Division = {
         id = { type = 12700 id = 9002 }
         name = "4th Indian Division"
         type = infantry
         model = 7
         strength = 100
      }
      Division = {
         id = { type = 12700 id = 9005 }
         name = "Madras Brigade"
         type = militia
         model = 2
         extra = artillery
         brigade_model = 1
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9011 }
         name = "Poona Brigade"
         type = garrison
         model = 2
         strength = 80
      }
   }

   landunit = {
      name = "II Western Corps"
      location = 1517
      leader = 250070
      id = { type = 12700 id = 9004 }
      Division = {
         id = { type = 12700 id = 9007 }
         name = "Mhow Brigade"
         type = militia
         model = 2
         extra = artillery
         brigade_model = 1
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9009 }
         name = "Deccan Brigade"
         type = militia
         model = 3
         extra = artillery
         brigade_model = 2
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9003 }
         name = "4th Indian Cavalry Brigade"
         type = cavalry
         model = 8
         strength = 15
      }
   }

   landunit = {
      name = "III Eastern Corps"
      location = 1447
      leader = 250074
      id = { type = 12700 id = 9012 }
      Division = {
         id = { type = 12700 id = 9013 }
         name = "3rd Indian Division"
         type = infantry
         model = 7
         strength = 100
      }
      Division = {
         id = { type = 12700 id = 9016 }
         name = "Eastern Bengal Brigade"
         type = militia
         model = 2
         extra = artillery
         brigade_model = 1
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9017 }
         name = "Assam Brigade"
         type = militia
         model = 2
         strength = 80
      }
   }

   landunit = {
      name = "IV Central Corps"
      location = 1461
      leader = 251001
      id = { type = 12700 id = 9018 }
      Division = {
         id = { type = 12700 id = 9019 }
         name = "Allahabad Brigade"
         type = militia
         model = 2
         extra = artillery
         brigade_model = 1
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9020 }
         name = "Lucknow Brigade"
         type = militia
         model = 2
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9014 }
         name = "3rd Indian Cavalry Brigade"
         type = cavalry
         model = 8
         strength = 15
      }
   }

   landunit = {
      name = "V Delhi Corps"
      location = 1459
      leader = 251002
      id = { type = 12700 id = 9021 }
      Division = {
         id = { type = 12700 id = 9022 }
         name = "Delhi Brigade"
         type = garrison
         model = 2
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9024 }
         name = "Meerut Brigade"
         type = militia
         model = 3
         extra = artillery
         brigade_model = 2
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9055 }
         name = "Rawalpindi Brigade"
         type = militia
         model = 3
         extra = artillery
         brigade_model = 2
         strength = 80
      }
   }

   landunit = {
      name = "VI Baluchistan Corps"
      location = 1529
      leader = 251003
      id = { type = 12700 id = 9025 }
      Division = {
         id = { type = 12700 id = 9026 }
         name = "Zhob Brigade"
         type = garrison
         model = 2
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9028 }
         name = "Quetta Brigade"
         type = militia
         model = 3
         extra = artillery
         brigade_model = 2
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9029 }
         name = "Khojak Brigade"
         type = militia
         model = 3
         strength = 80
      }
   }

   landunit = {
      name = "VII Indus Corps"
      location = 1533
      leader = 251004
      id = { type = 12700 id = 9030 }
      Division = {
         id = { type = 12700 id = 9031 }
         name = "Sind Brigade"
         type = garrison
         model = 2
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9035 }
         name = "2nd Indian Cavalry Brigade"
         type = cavalry
         model = 8
         strength = 15
      }
      Division = {
         id = { type = 12700 id = 9041 }
         name = "Ambala Brigade"
         type = militia
         model = 3
         strength = 80
      }
   }

   landunit = {
      name = "VIII Northern Corps"
      location = 1534
      leader = 251007
      id = { type = 12700 id = 9032 }
      Division = {
         id = { type = 12700 id = 9033 }
         name = "1st Indian Division"
         type = infantry
         model = 7
         strength = 100
      }
      Division = {
         id = { type = 12700 id = 9034 }
         name = "2nd Indian Division"
         type = infantry
         model = 7
         strength = 100
      }
      Division = {
         id = { type = 12700 id = 9037 }
         name = "Sialkot Brigade"
         type = militia
         model = 3
         extra = artillery
         brigade_model = 2
         strength = 80
      }
   }

   landunit = {
      name = "IX Lahore Corps"
      location = 1530
      leader = 251009
      id = { type = 12700 id = 9036 }
      Division = {
         id = { type = 12700 id = 9038 }
         name = "Ferozepore Brigade"
         type = militia
         model = 3
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9039 }
         name = "Jullundur Brigade"
         type = militia
         model = 3
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9040 }
         name = "Lahore Brigade"
         type = militia
         model = 3
         strength = 80
      }
   }

   landunit = {
      name = "X Waziristan Corps"
      location = 1537
      leader = 251014
      id = { type = 12700 id = 9042 }
      Division = {
         id = { type = 12700 id = 9043 }
         name = "Razmak Brigade"
         type = militia
         model = 2
         extra = artillery
         brigade_model = 1
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9044 }
         name = "Bannu Brigade"
         type = militia
         model = 2
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9045 }
         name = "Wana Brigade"
         type = militia
         model = 2
         strength = 80
      }
   }

   landunit = {
      name = "XI Peshawar Corps"
      location = 1537
      leader = 250171
      id = { type = 12700 id = 9049 }
      Division = {
         id = { type = 12700 id = 9050 }
         name = "Landikotal Brigade"
         type = militia
         model = 3
         extra = artillery
         brigade_model = 2
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9051 }
         name = "Peshawar Brigade"
         type = militia
         model = 3
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9052 }
         name = "Nowshera Brigade"
         type = militia
         model = 3
         strength = 80
      }
   }

   landunit = {
      name = "XII Kohat Mobile Group"
      location = 1537
      leader = 250148
      id = { type = 12700 id = 9046 }
      Division = {
         id = { type = 12700 id = 9047 }
         name = "Thal Brigade"
         type = militia
         model = 2
         extra = artillery
         brigade_model = 1
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9048 }
         name = "Kohat Brigade"
         type = militia
         model = 2
         strength = 80
      }
      Division = {
         id = { type = 12700 id = 9053 }
         name = "1st Indian Cavalry Brigade"
         type = cavalry
         model = 8
         strength = 15
      }
   }

   landunit = {
      name = "Jammu & Kashmir State Forces"
      location = 1540
      id = { type = 12700 id = 9056 }
      Division = {
         id = { type = 12700 id = 9057 }
         name = "Jammu Brigade"
         type = militia
         model = 2
         strength = 100
         locked = yes
      }
      Division = {
         id = { type = 12700 id = 9058 }
         name = "Kashmir Brigade"
         type = militia
         model = 2
         strength = 100
         locked = yes
      }
   }

   landunit = {
      name = "Gwalior State Forces"
      location = 1523
      id = { type = 12700 id = 9059 }
      Division = {
         id = { type = 12700 id = 9060 }
         name = "Gwalior Cavalry Brigade"
         type = cavalry
         model = 6
         strength = 45
         locked = yes
      }
      Division = {
         id = { type = 12700 id = 9061 }
         name = "Gwalior Infantry Brigade"
         type = militia
         model = 2
         strength = 100
         locked = yes
      }
   }

   landunit = {
      name = "Hyderabad State Forces"
      location = 1487
      id = { type = 12700 id = 9062 }
      Division = {
         id = { type = 12700 id = 9063 }
         name = "Hyderabad State Forces"
         type = militia
         model = 2
         strength = 100
         locked = yes
      }
   }

   landunit = {
      name = "Bikaner State Forces"
      location = 1527
      id = { type = 12700 id = 9064 }
      Division = {
         id = { type = 12700 id = 9065 }
         name = "Bikaner State Forces"
         type = militia
         model = 2
         strength = 80
         locked = yes
      }
   }

   landunit = {
      name = "Patiala State Forces"
      location = 1531
      id = { type = 12700 id = 9066 }
      Division = {
         id = { type = 12700 id = 9067 }
         name = "Patiala State Forces"
         type = militia
         model = 2
         strength = 80
         locked = yes
      }
   }

   landunit = {
      name = "Mysore State Forces"
      location = 1507
      id = { type = 12700 id = 9068 }
      Division = {
         id = { type = 12700 id = 9069 }
         name = "Mysore State Forces"
         type = militia
         model = 2
         strength = 70
         locked = yes
      }
   }

   landunit = {
      name = "Burma Independent District"
      location = 1415
      id = { type = 12700 id = 9070 }
      Division = {
         id = { type = 12700 id = 9071 }
         name = "Burma Brigade"
         type = militia
         model = 2
         extra = artillery
         brigade_model = 1
         strength = 80
      }
   }
'@ -replace "`n", "`r`n"

$scenario = $scenario.Substring(0, $start) + $landForces.TrimEnd() + "`r`n`t" + $scenario.Substring($end)
[System.IO.File]::WriteAllText($scenarioPath, $scenario, $encoding)

$leaders = [System.IO.File]::ReadAllText($leaderPath, $encoding)
$promotions = @{
    "250021" = "1933"
    "250070" = "1933"
    "250074" = "1933"
    "251001" = "1933"
    "251002" = "1933"
    "251003" = "1933"
    "251004" = "1933"
    "251007" = "1933"
    "251009" = "1933"
    "251014" = "1933"
}

$rows = $leaders -split "\r?\n"
for ($i = 1; $i -lt $rows.Count; $i++) {
    if ([string]::IsNullOrWhiteSpace($rows[$i])) {
        continue
    }

    $fields = $rows[$i].Split(";")
    if ($fields.Count -lt 5 -or -not $promotions.ContainsKey($fields[1])) {
        continue
    }

    $fields[4] = $promotions[$fields[1]]
    $rows[$i] = $fields -join ";"
}

[System.IO.File]::WriteAllText($leaderPath, (($rows -join "`r`n").TrimEnd() + "`r`n"), $encoding)
Write-Host "Applied AUBM V4 corps organization and 1933 command promotions."
