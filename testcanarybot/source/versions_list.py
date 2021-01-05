main = []
beta_versions = {
    1.0: [0.96, 0.97]
}

beta = []

for i in beta_versions.keys(): beta.extend(beta_versions[i])

supporting = [*main, *beta]
supporting.sort()

current = supporting[-1]