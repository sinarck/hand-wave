import random
#randomly samples from youtube asl dataset

# CONFIGURATION
input_path = '../data/youtube_asl_video_ids.txt'  # Path to the full video IDs file
output_path = 'sampled_youtube_asl_ids.txt'      # Output file for sampled IDs
sample_size = 1000                               # Number of IDs to sample (change as needed)


def main():
    # Read all video IDs
    with open(input_path, 'r') as f:
        video_ids = [line.strip() for line in f if line.strip()]

    # Randomly sample IDs
    sampled_ids = random.sample(video_ids, min(sample_size, len(video_ids)))

    # Write sampled IDs to output file
    with open(output_path, 'w') as f:
        for vid in sampled_ids:
            f.write(vid + '\n')

    print(f"Sampled {len(sampled_ids)} video IDs written to {output_path}")


if __name__ == '__main__':
    main() 