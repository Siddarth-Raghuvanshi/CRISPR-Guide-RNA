"""
Entry point to the program

- Accept and parse user commands
- Generate Potential Guides
- Run through biophysical model and report results
"""
import argparse
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import guide_generator
import guide_strength_calculator

FASTA_FILE = "../output/Run_Genome_Plus_RC"

def init_parser():
    """
    Initializes a parser to get user arguments using argparse

    Returns:
        ArgumentParser -- parser ready to accept arguments
    """
    # Parser to get the files listed in the arguments
    parser = argparse.ArgumentParser(description="""This program helps you to find all possible guide RNAs that will \n
                                       target the gene. Then using the model created by Salis Lab, \n
                                       you can see the off target effects for the each possible guide.""",
                                     formatter_class=argparse.RawTextHelpFormatter)

    # Parsers to add arguements.
    parser.add_argument("-t", "--target_sequence", required=True,
                        help="The Gene Sequence of Interest (Fasta or Genebank)")
    parser.add_argument("-g", "--genome_sequence", required=True, nargs='+',
                        help="""The Genome of the organism, if targeting a plasmid, make sure to \n
                              include it as well (Fasta or Genebank)""")
    parser.add_argument("-a", "--azimuth_cutoff", required=False, default=10,
                        help="""How many guides should pass from azimuth screening,
                              the guides are passed based on descending azimuth prediction score""")
    parser.add_argument("-o", "--output_name", required=False, default="output",
                        help="The name of the output file generated by the program")
    parser.add_argument("-p", "--purpose", required=False, default="d",
                        help="""i: CRISPR interference on gene
                             # g: guide binding strength calculator
                             # Leave blank to see all possible guides and off target effects from your sequence""")
    parser.add_argument("-threads", required=False, default=None, type=int,
                        help="""Number of threads to use when running the program""")

    return parser

def get_sequence(args):
    """
    Returns the upper case sequences as strings from the files given as arguments.
    Also combines the various genome sequences
    """
    # Reads the file using biopython and creates a object called target
    # target_dict = SeqIO.to_dict(SeqIO.parse(
    #     args.target_sequence, args.target_sequence.split('.')[-1]))

    target_dict = SeqIO.to_dict(SeqIO.parse(
        args.target_sequence, "fasta"))
    for name in target_dict:
        target_dict[name] = target_dict[name].seq.upper()

    # Reads the Genome files using biopython and combines them into one genome object
    genome = SeqRecord(Seq(""))
    for i in range(len(args.genome_sequence)):
        genome_parts = SeqIO.parse(
            args.genome_sequence[i], "fasta")
        for part in genome_parts:
            genome.seq = genome.seq + part.seq

    return target_dict, genome.seq.upper()

def main():
    """
    Main workflow
    """
    parser = init_parser()

    # Creating a variable to make the values easily accessible
    args = parser.parse_args()

    # Get the sequences in a Seq format from user fasta or genebank files
    target_dict, genome = get_sequence(args)

    ref_record = SeqRecord(genome, id="refgenome", name="reference", description="a reference background")
    ref_record = ref_record + ref_record.reverse_complement()
    SeqIO.write(ref_record, FASTA_FILE, "fasta")

    # Select the guides based on the purpose and the azimuth model
    guide_list = guide_generator.select_guides(target_dict, args)
    # Build and run the model
    guide_strength_calculator.initialize_logger(args.output_name)
    results_df = guide_strength_calculator.initalize_model(guide_list, FASTA_FILE, num_threads=args.threads)

    results_df.to_csv("../output/" + args.output_name + ".csv", index=False)

if __name__ == "__main__":
    main()
