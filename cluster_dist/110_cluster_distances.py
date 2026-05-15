#!/usr/bin/env python3
"""
Calculate pairwise cluster-cluster similarity and distance from DP-GP
posterior similarity matrix.

Uses vectorized numpy operations for speed on the 19K x 19K matrix.
Handles the name mapping between the similarity matrix (Gene_tussie_unique)
and the clustering file (Gene_tussie) via the merged annotation CSV.

cluster distance calculation formula: cluster_dist/formula.jpg

Outputs:
  - cluster_similarity_matrix.tsv  (S(Ca, Cb) = mean P(zi=zj) for i in Ca, j in Cb)
  - cluster_distance_matrix.tsv    (D = 1 - S)
  - cluster_distance_heatmap.png
  - cluster_dendrogram.png
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import linkage, dendrogram
import os
import time

# ── File paths ──────────────────────────────────────────────────────────
BASE = "tissue_all/clustering_full"

CLUSTERING_FILE = os.path.join(BASE, "tissue_all_optimal_clustering.txt")
SIMILARITY_FILE = os.path.join(
    BASE,
    "tissue_all_posterior_similarity_matrix_reformatted_unique_ID.txt",
)
MAPPING_CSV = os.path.join(
    BASE,
    "df_merged_genes_goterm_aspect_function_ageing_cluter_all_tissues_fully_clustered_"
    "similarity_stability_abundance_similarity_quantiles_shift_unique_identifier_"
    "with_nonparam_aging_cluster.csv",
)
OUTPUT_DIR = os.path.join(BASE, "cluster_distances")


def build_name_mapping(mapping_csv):
    """Return dict: Gene_tussie_unique -> Gene_tussie."""
    df = pd.read_csv(mapping_csv, usecols=["Gene_tussie_unique", "Gene_tussie"])
    return dict(zip(df["Gene_tussie_unique"], df["Gene_tussie"]))


def load_clustering(clustering_file):
    """Return (gene_to_cluster dict, unique_clusters sorted array)."""
    df = pd.read_csv(clustering_file, sep="\t")
    gene_to_cluster = dict(zip(df["gene"], df["cluster"]))
    unique_clusters = np.sort(df["cluster"].unique())
    print(f"Loaded {len(gene_to_cluster)} genes in {len(unique_clusters)} clusters")
    return gene_to_cluster, unique_clusters


def calculate_cluster_similarity(sim_matrix, cluster_labels, unique_clusters):
    """
    Vectorized cluster-cluster similarity:
        S(Ca, Cb) = (1 / |Ca||Cb|) * sum_{i in Ca, j in Cb} P(zi = zj)

    Uses numpy fancy indexing to extract submatrices per cluster pair.
    """
    n_clusters = len(unique_clusters)
    similarity_matrix = np.zeros((n_clusters, n_clusters))

    # Pre-compute index arrays for each cluster
    cluster_idx = {}
    for k, c in enumerate(unique_clusters):
        cluster_idx[k] = np.where(cluster_labels == c)[0]

    total_pairs = n_clusters * (n_clusters - 1) // 2
    done = 0

    for i in range(n_clusters):
        idx_i = cluster_idx[i]
        # Diagonal: intra-cluster similarity
        sub = sim_matrix[np.ix_(idx_i, idx_i)]
        similarity_matrix[i, i] = sub.mean()

        for j in range(i + 1, n_clusters):
            idx_j = cluster_idx[j]
            # Extract submatrix and compute mean in one shot
            sub = sim_matrix[np.ix_(idx_i, idx_j)]
            avg_sim = sub.mean()
            similarity_matrix[i, j] = avg_sim
            similarity_matrix[j, i] = avg_sim

            done += 1
            if done % 500 == 0:
                print(f"  {done}/{total_pairs} pairs computed...")

    return similarity_matrix


def plot_distance_heatmap(distance_matrix, cluster_labels, output_file):
    labels = [f"{c}" for c in cluster_labels]
    fig, ax = plt.subplots(figsize=(18, 16))
    sns.heatmap(
        distance_matrix,
        xticklabels=labels,
        yticklabels=labels,
        cmap="viridis",
        square=True,
        cbar_kws={"label": "Distance (1 - similarity)"},
        ax=ax,
    )
    ax.set_title("Pairwise Cluster Distance (1 - posterior co-clustering similarity)")
    ax.tick_params(axis="both", labelsize=5)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Heatmap saved to {output_file}")


def plot_dendrogram(distance_matrix, cluster_labels, output_file):
    condensed = squareform(distance_matrix, checks=False)
    Z = linkage(condensed, method="average")

    fig, ax = plt.subplots(figsize=(20, 8))
    dendrogram(
        Z,
        labels=[f"C{c}" for c in cluster_labels],
        orientation="top",
        leaf_rotation=90,
        leaf_font_size=6,
        ax=ax,
    )
    ax.set_title("Hierarchical Clustering of Clusters (average linkage)")
    ax.set_ylabel("Distance (1 - similarity)")
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Dendrogram saved to {output_file}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Build name mapping: unique_ID -> Gene_tussie
    print("Loading name mapping...")
    name_map = build_name_mapping(MAPPING_CSV)
    print(f"  {len(name_map)} entries in mapping")

    # 2. Load clustering assignments
    gene_to_cluster, unique_clusters = load_clustering(CLUSTERING_FILE)

    # 3. Load posterior similarity matrix (1.9 GB, ~3 GB in RAM as float64)
    print("Loading posterior similarity matrix (this may take a few minutes)...")
    t0 = time.time()
    sim_df = pd.read_csv(SIMILARITY_FILE, sep="\t", index_col=0)
    print(f"  Loaded in {time.time() - t0:.0f}s, shape: {sim_df.shape}")

    # 4. Map similarity matrix rows to clustering gene names
    sim_unique_ids = list(sim_df.index)
    sim_gene_names = [name_map.get(uid, uid) for uid in sim_unique_ids]

    # Build cluster label array aligned to similarity matrix row order
    cluster_labels_aligned = []
    unmapped = 0
    for gname in sim_gene_names:
        if gname in gene_to_cluster:
            cluster_labels_aligned.append(gene_to_cluster[gname])
        else:
            cluster_labels_aligned.append(-1)
            unmapped += 1

    cluster_labels_aligned = np.array(cluster_labels_aligned)
    if unmapped > 0:
        print(f"  Warning: {unmapped} genes in similarity matrix not found in clustering")

    # Drop unmapped genes
    valid_mask = cluster_labels_aligned != -1
    sim_matrix = sim_df.values[np.ix_(valid_mask, valid_mask)]
    cluster_labels_aligned = cluster_labels_aligned[valid_mask]
    print(f"  Using {valid_mask.sum()} genes ({unmapped} dropped)")

    # 5. Compute cluster-cluster similarity (vectorized)
    print("Computing cluster-cluster similarity matrix...")
    t0 = time.time()
    sim_cc = calculate_cluster_similarity(sim_matrix, cluster_labels_aligned, unique_clusters)
    print(f"  Done in {time.time() - t0:.1f}s")

    # 6. Convert to distance
    dist_cc = 1.0 - sim_cc

    # 7. Save outputs
    cluster_strs = [f"Cluster_{c}" for c in unique_clusters]

    sim_out = os.path.join(OUTPUT_DIR, "cluster_similarity_matrix.tsv")
    pd.DataFrame(sim_cc, index=cluster_strs, columns=cluster_strs).to_csv(sim_out, sep="\t")
    print(f"Similarity matrix saved to {sim_out}")

    dist_out = os.path.join(OUTPUT_DIR, "cluster_distance_matrix.tsv")
    pd.DataFrame(dist_cc, index=cluster_strs, columns=cluster_strs).to_csv(dist_out, sep="\t")
    print(f"Distance matrix saved to {dist_out}")

    # 8. Plots
    plot_distance_heatmap(dist_cc, unique_clusters,
                          os.path.join(OUTPUT_DIR, "cluster_distance_heatmap.png"))
    plot_dendrogram(dist_cc, unique_clusters,
                    os.path.join(OUTPUT_DIR, "cluster_dendrogram.png"))

    # 9. Summary
    print(f"\n=== Summary ===")
    print(f"Clusters: {len(unique_clusters)}")
    print(f"Min distance: {dist_cc[dist_cc > 0].min():.4f}")
    print(f"Max distance: {dist_cc.max():.4f}")
    print(f"Mean distance: {dist_cc[np.triu_indices_from(dist_cc, k=1)].mean():.4f}")

    # Show top-5 most similar cluster pairs
    triu_i, triu_j = np.triu_indices_from(sim_cc, k=1)
    pair_sims = sim_cc[triu_i, triu_j]
    top5 = np.argsort(pair_sims)[::-1][:5]
    print("\nTop 5 most similar cluster pairs:")
    for rank, idx in enumerate(top5):
        ci, cj = unique_clusters[triu_i[idx]], unique_clusters[triu_j[idx]]
        print(f"  {rank+1}. Cluster {ci} <-> Cluster {cj}: "
              f"similarity={pair_sims[idx]:.4f}, distance={1-pair_sims[idx]:.4f}")


if __name__ == "__main__":
    main()

