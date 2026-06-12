
[![Build Status](https://travis-ci.org/ReddyLab/DP_GP_cluster.svg?branch=master)](https://travis-ci.org/ReddyLab/DP_GP_cluster)

## DP_GP_cluster (proteomics fork)

Methodology clusters dataset samples by abundance patternt over a time course using a Dirichlet process Gaussian process model.

This fork implements the clustering methodology described in the paper [*"Endocytic Turnover of Endothelial Cell-Membrane Proteins as a Driver of Rat Blood Brain Barrier Specialization and Dysfunction"* (ISCIENCE-D-25-18428R1)](https://doi.org/10.1016/j.isci.2026.116231).


**About this fork.** 
> This repository is a **Python 3** port of the original [PrincetonUniversity/DP_GP_cluster](https://github.com/PrincetonUniversity/DP_GP_cluster) (Python 2), adapted here for **proteomics** time-course data mirroring the [methodology developed for RNA-seq microarray gene expression](https://doi.org/10.1371/journal.pcbi.1005896). <br>
The input domain, plot labels are proteomics-specific, and a cluster-distance utility is a universal add-on suitable for any feature set.<br>
Throughout this README and the upstream code, "gene" / "gene expression" are interchangebly used with **proteins** / **protein abundance**, since in our dataset protein unique identifies are constructed including their protein-encoding gene names, we leave varaiable and functions with gene naming convention in deep code scripts, where it doesn't affect output.<br>
Plot y-axes in this version are labeled `Protein abundance` for a more consistent user output.

Proteomics-fork additions:
- **Inter-cluster distance** — see the [Inter-cluster distance](#inter-cluster-distance) section.
- **Long-running job monitoring** — optional logging and auto-restart wrappers for multi-day runs, see [Long-running jobs and monitoring](#long-running-jobs-and-monitoring).
For short runs simply use `DP_GP_cluster.py` directly; monitoring is *not* required.

## Motivation

Evidence indicates that the endocytic dynamics of proteins, particularly how long a protein resides at the plasma membrane, play an important role in determining cellular behavior. Endocytic dynamics refers to the patterns by which proteins are internalized, recycled, and degraded, and it contains information about membrane protein regulation. Despite this, it remains largely unknown whether brain endothelial cells (BECs) have a distinct endocytic signature that contributes to their specialized phenotype.
For this reason, and for the first time in this context, we cluster proteins originated from peripheral, healthy brain and inflamed brain tissues in order to identify unique endocytic profiles for individual proteins across phenotypes, and quantitatively estimate differences that characterize healthy brain phenotype, and how protein behavior changes with inflammation.
Even though parametric (linear) modeling detects endocytic profile differences between brain and peripheral, it oversimplifies complex endocytic patterns which may contain important biological information. Therefore, we implemented a non-parametric modeling approach allowing us to: (1) determine the optimal number of clusters employing a [Dirichlet process](http://en.wikipedia.org/wiki/Dirichlet_process), while iteratively (2) modeling the trajectory and time-dependency of protein abundance via a [Gaussian process](http://en.wikipedia.org/wiki/Gaussian_process).

## Installation and Dependencies
1. create and activate conda/mamba environment
```bash
mamba create -n DP_GP-env python=3.10
mamba activate DP_GP-env
```
2. Install Cython and numpy
```bash
mamba install -c conda-forge Cython numpy
```
3. Clone repo
```bash
git clone https://github.com/Molecular-Bionics-Labs/DP_GP_cluster_proteomics.git
```
4. Use pip for installation
```bash
cd path/to/DP_GP_cluster
pip install .
```

DP_GP_cluster requires the following automatically installed Python packages:
    
    GPy, pandas, numpy, scipy (>= 0.14), matplotlib.pyplot

It has been tested in linux with Python 3.10 and with Anaconda distributions of the latter four above packages.


## Tests

    cd DP_GP_cluster
    DP_GP_cluster.py -i test/test.txt -o test/test -p png -n 20 --plot

## Code Examples

To cluster proteins by abundance over time course and create protein-by-protein posterior similarity matrix:
    
    DP_GP_cluster.py -i /path/to/abundance.txt -o /path/to/output_prefix [ optional args, e.g. -n 2000 --true_times --criterion MAP --plot ... ]
    
Above, `abundance.txt` is of the format:

    protein    1     2    3    ...    time_t
    protein_1  10    20   5    ...    8
    protein_2  3     2    50   ...    8
    protein_3  18    100  10   ...    22
    ...
    protein_n  45    22   15   ...    60

where the first row is a header containing the time points and the first column is an index containing all protein names. Entries are delimited by tabs.

DP_GP_cluster can handle missing data so if an abundance value for a given protein at a given time point leave blank or represent with "NA".
For the proteomics dataset we avoid using samples with missing data to prevent biased data imputation.

McDowell et al recommended clustering only differentially expressed genes/proteins to save runtime. For large datasets, common for proteomics studies, we overcome this limitation having developed a script for realiable multi-day runs with timestamped logs, memory tracking, an 83-hour timeout guard, crashes detector and restart-on-crush option. It is described in [Long-running jobs and monitoring] section

Alternatively, to cluster thousands of genes/ proteins, legacy option `--fast` exist, although in this mode, no missing data allowed. We recommend to run the full cycle in monitored mode.

From the above command, the optimal clustering will be saved at `/path/to/output_path_prefix_optimal_clustering.txt` in a simple tab-delimited format:

    cluster	protein
    1	protein_1
    1	protein_23
    2	protein_7
    ...
    k	protein_30
    
Because the optimal clustering is chosen after the entirety of Gibbs sampling, the script can be rerun with alternative clustering optimality criteria to yield different sets of clusters. Also, if `--plot` flag was not indicated when the above script is called, plots can be generated after sampling:

    DP_GP_cluster.py \
    -i /path/to/abundance.txt \
    --sim_mat /path/to/output_prefix_posterior_similarity_matrix.txt \
    --clusterings /path/to/output_prefix_clusterings.txt \
    --criterion MPEAR \
    --post_process \
    --plot --plot_types png,pdf \
    --output /path/to/output_prefix_MPEAR_optimal_clustering.txt \
    --output_path_prefix /path/to/output_prefix_MPEAR

When the `--plot` flag is indicated, the script plots (1) abundance trajectories by cluster along with the Gaussian Process parameters of each cluster and (2) the posterior similarity matrix in the form of a heatmap with dendrogram. For example:

#### Protein abundance trajectories by cluster*
![expression](auxiliary/tissue_all_gene_expression_fig_1.png =500x)

*supplement for [Tomás-Sitjes et al. 2026. Endocytic turnover of endothelial cell-membrane proteins as a driver of rat blood-brain barrier specialization and dysfunction. iScience, 29(6), 116231](https://doi.org/10.1016/j.isci.2026.116231)

#### Posterior similarity matrix**
![PSM](auxiliary/tissue_all_posterior_similarity_matrix_heatmap.png =500x)

**supplement for [Tomás-Sitjes et al. 2026. Endocytic turnover of endothelial cell-membrane proteins as a driver of rat blood-brain barrier specialization and dysfunction. iScience, 29(6), 116231](https://doi.org/10.1016/j.isci.2026.116231)

For more details on particular parameters, see detailed help message in script.

### Using DP_GP functions without wrapper script

Users have the option of directly importing DP_GP for direct access to functions. For example,
    
    from DP_GP import core
    import GPy
    from DP_GP import cluster_tools
    import numpy as np
    from collections import defaultdict

    abundance = "/path/to/abundance.txt"
    optimal_clusters_out = "/path/to/optimal_clusters.txt"

    # read in protein abundance matrix
    protein_abundance_matrix, protein_names, t, t_labels = core.read_protein_abundance_matrices([abundance])

    # run Gibbs Sampler
    GS = core.gibbs_sampler(protein_abundance_matrix, t, 
                            max_num_iterations=200, 
                            burnIn_phaseI=50, burnIn_phaseII=100)
    sim_mat, all_clusterings, sampled_clusterings, log_likelihoods, iter_num = GS.sampler()

    sampled_clusterings.columns = protein_names
    all_clusterings.columns = protein_names

    # select best clustering by maximum a posteriori estimate
    optimal_clusters = cluster_tools.best_clustering_by_log_likelihood(np.array(sampled_clusterings), 
                                                                       log_likelihoods)

    # combine protein_names and optimal_cluster info
    optimal_cluster_labels = defaultdict(list)
    optimal_cluster_labels_original_protein_names = defaultdict(list)
    for protein, (protein_name, cluster) in enumerate(zip(protein_names, optimal_clusters)):
        optimal_cluster_labels[cluster].append(protein)
        optimal_cluster_labels_original_protein_names[cluster].append(protein_name)

    # save optimal clusters
    cluster_tools.save_cluster_membership_information(optimal_cluster_labels_original_protein_names, optimal_clusters_out)

With this approach, the user will have access to the GP models parameterized to each cluster. With this, the user could, e.g., draw samples from a cluster GP or predict a new abundance value at a new time point along with the associated uncertainty.

    # [continued from above]
    # optimize GP model for best clustering
    optimal_clusters_GP = {}
    for cluster, proteins in optimal_cluster_labels.iteritems():
        optimal_clusters_GP[cluster] = core.dp_cluster(members=proteins, 
                                                       X=np.vstack(t), 
                                                       Y=np.array(np.mat(protein_abundance_matrix[proteins,:])).T)
        optimal_clusters_GP[cluster] = optimal_clusters_GP[cluster].update_cluster_attributes(protein_abundance_matrix)

    def draw_samples_from_cluster_GP(cluster_GP, n_samples=1):
        samples = np.random.multivariate_normal(cluster_GP.mean, cluster_GP.covK, n_samples)    
        return samples

    def predict_new_y_from_cluster_GP(cluster_GP, new_x):
        next_time_point = np.vstack([cluster_GP.t, new_x])
        mean, var = cluster_GP.model._raw_predict(next_time_point)
        y, y_var = float(mean[-1]), float(var[-1])
        return y, y_var

    draw_samples_from_cluster_GP(optimal_clusters_GP[1])
    predict_new_y_from_cluster_GP(optimal_clusters_GP[2], new_x=7.2)

    
## Inter-cluster distance

After Gibbs sampling produces an optimal clustering and a protein-by-protein posterior
similarity matrix $P(z_i = z_j| data)$, 

We can define cluster-cluster similarity for clusters $C_a$ and $C_b$ by summarizing how close two clusters are by
averaging the pairwise posterior co-clustering probabilities of their members:

$$S(C_a, C_b) = \frac{1}{|C_a||C_b|} \cdot \sum_{i ∈ C_a} \sum_{j ∈ C_b}  P(z_i = z_j)$$

Therefore, distance when needed is additive inverse:
$$D(C_a, C_b) = 1 − S(C_a, C_b)$$


The implementation is in [`cluster_dist/110_cluster_distances.py`](cluster_dist/110_cluster_distances.py).
It is vectorized with `numpy.ix_` and is intended for large similarity matrices
(tested on a 19 K × 19 K matrix). Outputs:

- `cluster_similarity_matrix.tsv` — $S(C_a, C_b)$
- `cluster_distance_matrix.tsv` — $D = 1 − S$
- `cluster_distance_heatmap.png`
- `cluster_dendrogram.png` (average-linkage hierarchy on `D`)

Adjust the `BASE` / input paths at the top of the script for your data, then:

```bash
python cluster_dist/110_cluster_distances.py
```

![cluster_dist](auxiliary/cluster_dendrogram.png =1000x)
***supplement for [Tomás-Sitjes et al. 2026. Endocytic turnover of endothelial cell-membrane proteins as a driver of rat blood-brain barrier specialization and dysfunction. iScience, 29(6), 116231](https://doi.org/10.1016/j.isci.2026.116231)

## Long-running jobs and monitoring

Gibbs sampling over thousands of samples and features can take **days** to converge. To make
overnight / multi-day runs reliable, this repo ships an optional monitoring
layer in described in [`MONITORING.md`](MONITORING.md):

- **`run_dp_gp_monitored.sh`** — wrapper around `DP_GP_cluster.py` that adds
  timestamped logs, memory / disk tracking, signal handling, an 83-hour timeout
  guard, and optional email / Slack / GitHub-issue notifications on
  start / finish / crash.
- **`monitor_dp_gp.sh --auto-restart`** — external watchdog that detects a
  crashed run and restarts it (configurable max attempts), so a single OOM or
  transient error does not waste the whole run.
- **`setup_monitoring.sh`** — interactive first-time setup for the
  notification channels.

Typical multi-day workflow:

```bash
./setup_monitoring.sh                                       # one-time
./monitor_dp_gp.sh --auto-restart --max-attempts=5 &
./run_dp_gp_monitored.sh
```

All logs land in `logs/` (`dp_gp_*.log`, `monitor_*.log`). See
[`MONITORING.md`](MONITORING.md) for the full feature list, notification config,
troubleshooting tips, and recovery commands.

The monitoring layer is **optional**, but allow for more stable results than `--fast` option for large datasets.
For short runs simply use `DP_GP_cluster.py` directly.

## Citation

If you use this proteomics fork, please cite:

Tomás-Sitjes A, Arauz-Garofalo G, Gay M, Jarió S, Vilaseca M, Schastlivaia V, Kessen M, Manicardi N, Battaglia G, Gonzalez-Carter D, **Endocytic Turnover of Endothelial Cell-Membrane Proteins as a Driver of Rat Blood Brain Barrier Specialization and Dysfunction** _iScience. A Cell Press journal (2026)_ ISCIENCE-D-25-18428R1
[doi: 10.1016/j.isci.2026.116231](https://doi.org/10.1016/j.isci.2026.116231)

And the original DP_GP_cluster method:
<!-- 
*I. C. McDowell, D. Manandhar, C. M. Vockley, A. Schmid, T. E. Reddy, B. Engelhardt, Clustering gene expression time series data using an infinite Gaussian process mixture model.* _bioRxiv_ (2017) -->

McDowell I. C. , Manandhar D., Vockley C. M., Schmid A., Reddy T. E., Engelhardt B., **Clustering gene expression time series data using an infinite Gaussian process mixture model.** _PLOS Computational Biology (2018)_ [doi: 10.1371/journal.pcbi.1005896](https://doi.org/10.1371/journal.pcbi.1005896)

## License
[BSD 3-clause](https://github.com/PrincetonUniversity/DP_GP_cluster/blob/master/LICENSE)
    
