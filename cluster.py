import pysam
import re

class Position:
    """This class represents a genomic position.

    Methods:
    - to_string(): Returns a string representation of this position in the form
      "chrX:1000"
    """

    def __init__(self, chromosome, coordinate):
        self._chromosome = chromosome
        self._coordinate = coordinate

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return (self._chromosome == other._chromosome and
                self._coordinate == other._coordinate)

    def __hash__(self):
        return hash((self._chromosome, self._coordinate))

    def to_string(self):
        return self._chromosome + ":" + str(self._coordinate)


class Cluster:
    """This class represents a barcoding cluster as a collection of genomic
    positions.

    The underlying data structure is a set, so duplicate positions are
    discarded.

    Methods:
    - add_position(position): Adds a genomic position to this cluster

    - size(): Returns the number of reads or positions in this cluster

    - to_string(): Returns a string representation of this cluster as a
      tab-delimtited series of positions. See Position#to_string for how
      positions are represented as strings.
    """

    def __init__(self):
        self._positions = set()

    def add_position(self, position):
        self._positions.add(position)

    def size(self):
        return len(self._positions)

    def to_string(self):
        position_strings = [position.to_string() for position in self._positions]
        return "\t".join(position_strings)
        

class Clusters:
    """This class represents a collection of barcoding clusters.

    Methods:
    - get_cluster(barcodes): Returns the cluster that corresponds to the given
      barcode. If the cluster does not exist, it is initialized (with zero
      positions), and this empty cluster is returned.

    - add_position(barcodes, position): Adds the position to the cluster
      that corresponds with the given barcodes

    - to_strings(): Returns an iterator over the string representations of all
      of the contained clusters.
    """
    def __init__(self):
        self._clusters = {}

    def get_cluster(self, barcodes):
        if barcodes not in self._clusters:
            self._clusters[barcodes] = Cluster()
        return self._clusters[barcodes]

    def add_position(self, barcodes, position):
        self.get_cluster(barcodes).add_position(position)

    def to_strings(self):
        for barcodes, cluster in self._clusters.iteritems():
            yield barcodes + "\t" + cluster.to_string()

    def remove_cluster(self, barcodes):
        del self._clusters[barcodes]


def get_clusters(bamfile, num_barcodes):
    """Parses a BAM file, groups positions into clusters according to their
    barcodes, and returns the resulting structure.

    Each BAM record must have the barcodes stored in the query name like so:

    ORIGINAL_READ_NAME::[Barcode1][Barcode2][Barcode3]

    The individual barcodes should be enclosed in brackets and separated from
    the original read name with a double-colon.
    """

    clusters = Clusters()
    pattern = re.compile('::' + num_barcodes * '\[(\w+)\]')

    with pysam.AlignmentFile(bamfile, "rb") as f:

        for read in f.fetch(until_eof = True):
            position = Position(read.reference_name, read.reference_start)
            name = read.query_name
            match = pattern.search(name)
            barcodes = ".".join(match.groups())
            clusters.add_position(barcodes, position)

    return clusters


def write_clusters_to_file(clusters, outfile):
    """Writes a Clusters object to a file"""

    with open(outfile, 'w') as f:
        for cluster_string in clusters.to_strings():
            f.write(cluster_string)
            f.write("\n")
