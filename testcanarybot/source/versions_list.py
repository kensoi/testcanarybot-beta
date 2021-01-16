main = []
beta_versions = {
    1.0: [0.96, 0.97, 0.98, 0.981, 0.99]
}

beta = []

for i in beta_versions.keys(): beta.extend(beta_versions[i])

supporting = [*main, *beta]
supporting.sort()

current = supporting[-1]