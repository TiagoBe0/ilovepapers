# Figuras extraídas

**Fuente:** `/media/santi/ALMACEN_GRANDE_1/ilovepappers/pappers/ML_vacancias_difusion_HEA_Reimer_2025.pdf`
**Total figuras:** 29

---

## FIG_001 · Picture · Página 1

![fig_001](images/fig_001_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_002 · Picture · Página 1

![fig_002](images/fig_002_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_003 · Picture · Página 1

![fig_003](images/fig_003_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_004 · Picture · Página 1

![fig_004](images/fig_004_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_005 · Picture · Página 1

![fig_005](images/fig_005_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_006 · Picture · Página 1

![fig_006](images/fig_006_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_007 · Picture · Página 1

![fig_007](images/fig_007_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_008 · Picture · Página 1

![fig_008](images/fig_008_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_009 · Picture · Página 1

![fig_009](images/fig_009_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_010 · Picture · Página 1

![fig_010](images/fig_010_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_011 · Picture · Página 1

![fig_011](images/fig_011_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_012 · Picture · Página 2

![fig_012](images/fig_012_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_013 · Picture · Página 2

![fig_013](images/fig_013_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_014 · Picture · Página 2

![fig_014](images/fig_014_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_015 · Picture · Página 2

![fig_015](images/fig_015_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_016 · Picture · Página 2

![fig_016](images/fig_016_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_017 · Picture · Página 2

![fig_017](images/fig_017_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_018 · Picture · Página 2

![fig_018](images/fig_018_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_019 · Picture · Página 3

![fig_019](images/fig_019_FIG_1_The_workflow_used_in_this_work_.png)

**Caption:** FIG. 1. The workflow used in this work: (a) An MD HEA system produced trajectories from which two vacancy surroundings were extracted to compare the influence of various neighbouring atoms on vacancy transitions (Appendix A), (b) vacancy region datasets were converted to graph format, (c) the resulting dataset of states and chosen transition atoms was fed through a GCN to construct a trained model, and (d) model learned dynamics were used to generate accelerated synthetic trajectories of vacancy defect diffusion in the HEA system.

---

## FIG_020 · Picture · Página 5

![fig_020](images/fig_020_FIG_3_Network_structure_used_in_this_w.png)

**Caption:** FIG. 3. Network structure used in this work: (a) A graph input, (b) a convolutional layer that collects information on the host and neighbor nodes [white and black/blue/red in (b) respectively], (c) the output graph features and ReLU activation, (d) flattened node features from graph, (e) a linear layer with ReLU activation, and (f) an output layer that returns a single float value prediction for the rate constant per input atom/node. The tricolored graph nodes are stand-ins for one-hot encoded atom features such as those shown in Fig. 9(b).

---

## FIG_021 · Picture · Página 5

![fig_021](images/fig_021_FIG_2_Configurations_of_FCC_regions_of.png)

**Caption:** FIG. 2. Configurations of FCC regions of interest for the 1-NNI (upper right) and 2-NNI (lower right). In the 1-NNI model, the environment consists of 12 nearest-neighbor atoms of the vacancy, while in the 2-NNI model, the environment includes 54 atoms, incorporating both the first and second graph neighbors of the vacancy. The 12 allowed transition target atoms are colored in white.

---

## FIG_022 · Picture · Página 6

![fig_022](images/fig_022_FIG_4_Log-likelihood_loss_plots_for_bo.png)

**Caption:** FIG. 4. Log-likelihood loss plots for both EvoSys training setups. Training runs were plotted together as the unknown true dynamics of the MD system were the same in both setups, enabling direct comparison.

---

## FIG_023 · Picture · Página 7

![fig_023](images/fig_023_FIG_5_Mean_transition_preferences_per-.png)

**Caption:** FIG. 5. Mean transition preferences per-atom as a function of their fraction of the vacancy 1-NNI composition for each dataset (i.e., how often element ' X ' jumped when it occupied ' Y ' /12 of the allowed target atoms). Showing data for (a) MD training, (b) EvoSys 1-NNI, and (c) EvoSys 2-NNI datasets. Values presented in terms of difference with the MD baseline dataset.

---

## FIG_024 · Picture · Página 8

![fig_024](images/fig_024_FIG_7_Number_of_transition_events_dete.png)

**Caption:** FIG. 7. Number of transition events detected as a function of simulation realtime for the EvoSys 1-NNI and 2-NNI and MD (Baseline) setups. Faded EvoSys points indicate timing reported via from inside the Python script, in contrast to times reported from the bash script, which are presented in solid points.

---

## FIG_025 · Picture · Página 8

![fig_025](images/fig_025_FIG_6_Number_of_transition_events_dete.png)

**Caption:** FIG. 6. Number of transition events detected as a function of simulated time for EvoSys 1-NNI and 2-NNI and MD Baseline setups. Each plot shows the results of 10 trajectories.

---

## FIG_026 · Picture · Página 9

![fig_026](images/fig_026_FIG_8_ASD_measured_in_10_ps_intervals_.png)

**Caption:** FIG. 8. ASD measured in 10 ps intervals for each dataset, averaged across 10 trajectories. Shaded regions indicate standard deviation. Values are tabulated in Table IV .

---

## FIG_027 · Picture · Página 11

![fig_027](images/fig_027_FIG_9_NX_graph_representations_of_the_.png)

**Caption:** FIG. 9. NX graph representations of the vacancy defect 1-NNI environment: (a) A layout captured for an arbitrary vacancy state, showing node colors based on features (atom types) and node IDs from number tags assigned by OVITO; (b) an arbitrary vacancy graph layout for a binary alloy demonstrating the one-hot encoding scheme.

---

## FIG_028 · Picture · Página 11

![fig_028](images/fig_028_FIG_10_Histograms_of_vacancy_migration.png)

**Caption:** FIG. 10. Histograms of vacancy migration energy barriers for each elemental species (Fe, Ni, Cr, Co, and Cu) in the equiatomic FeNiCrCoCu HEA. The distributions represent the frequency of vacancy jump events as a function of energy barrier. Each histogram is fitted with a Gaussian distribution function, and the corresponding mean energy barrier for each element is reported.

---

## FIG_029 · Picture · Página 12

![fig_029](images/fig_029_Unique_Compositions_Ordered_by_Cu.png)

**Caption:** Unique Compositions (Ordered by Cu)
