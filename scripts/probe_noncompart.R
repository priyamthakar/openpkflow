.libPaths('D:/R-library/4.6')
library(NonCompart)
raw <- read.csv('D:/openpkflow/src/openpkflow/datasets/theoph.csv', stringsAsFactors=FALSE)
sub1 <- raw[raw$subject==1,]
r <- sNCA(sub1$time, sub1$conc, dose=sub1$dose[1], adm="Extravascular", dur=0, down="Log")
cat(paste(names(r), collapse=", "), "\n\n")
cat(paste(names(r), round(as.numeric(r),6), sep="=", collapse="\n"), "\n")
